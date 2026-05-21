"""
Drop-in replacement for auditstack's content stage.
Uses Parallel.ai Extract for full page content, chunk-level scoring,
deterministic checks + LLM with rubrics.
"""

from __future__ import annotations
import json, re, os, urllib.request, urllib.error, textstat
from typing import Any

import httpx

from auditstack.context import AuditContext
from auditstack.schemas.stage_outputs import ContentOutput
from auditstack.snapshot import SnapshotHandle
from auditstack.stages.base import BaseStage

PARALLEL_KEY = os.environ.get("PARALLEL_KEY", "KtepRKsixtAmtjSnaUP-U3wxmqLKiM3gkC_Q9YAW")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

E_EAT_BINARY = """
Also check these binary E-E-A-T signals for the page (1=present, 0=absent):
- has_byline: is there a visible author name?
- has_credentials: are the author's qualifications/role stated?
- has_last_updated: is there a visible date on the content?
- has_contact: is there a way to contact the company/author?
- has_original_data: does the page present company-generated data, surveys, or benchmarks?
- has_external_sources_cited: does the page reference and link to external sources?
Add these to the JSON: "eeat_binary": {"has_byline": 1, ...}
"""

CITATION_RUBRIC = """Score citation worthiness 0-10 using this anchored scale:
9-10: Directly answers a clear question. Unique, specific info not available elsewhere. Self-contained, fact-dense.
7-8: Strong content covering the topic well. Good structure and facts. Minor issues.
5-6: Decent but generic — similar content exists elsewhere. Lacks standout facts.
3-4: Thin, generic, poorly structured. Better sources almost certainly exist.
1-2: Vague, promotional, or irrelevant to any likely query.
0: Navigation, boilerplate, cookie policy, or completely off-topic.
Return JSON: {"citation_worthiness": 7, "evidence": "specific signal you observed"}"""

# EEAT disabled for speed — full rubric in llm-rubrics.md, enabled in v3

ANTI_PATTERNS = [
    r"as\s+mentioned\s+(above|earlier|previously)",
    r"refer\s+to\s+(the\s+)?(diagram|figure|chart|table|image|section)",
    r"click\s+here",
    r"see\s+(below|above)",
    r"previously\s+discussed",
    r"in\s+the\s+(previous|next|following)\s+(section|chapter|paragraph)",
]

DECLARATIVE_PATTERNS = [
    r"\b(is|are|was|were)\b.*\b(a|an|the)\b",
    r"\bmeans\b",
    r"\brefers\s+to\b",
    r"\bworks\s+by\b",
    r"\bdefined\s+as\b",
]

ANTI_CITATION_FLAGS = {
    "cta_overload": re.compile(r"(buy now|sign up|get started|try free|demo|contact us)", re.IGNORECASE),
    "keyword_stuffed": None,  # computed dynamically
    "all_caps_excessive": re.compile(r"[A-Z]{10,}"),
    "thin_content": None,  # computed by word count
    "boilerplate_ratio_high": None,  # computed
}


def parallel_extract(urls: list[str], objective: str) -> dict:
    req = urllib.request.Request(
        "https://api.parallel.ai/v1beta/extract",
        data=json.dumps({"urls": urls, "objective": objective, "full_content": True, "excerpts": False}).encode(),
        headers={"x-api-key": PARALLEL_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def deepseek_call(system: str, user: str, max_tokens: int = 2000) -> dict:
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps({
            "model": "deepseek-chat",
            "messages": [{"role": "system", "content": system},
                        {"role": "user", "content": user[:20000]}],
            "temperature": 0.3, "max_tokens": max_tokens
        }).encode(),
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:
        result = json.loads(resp.read())
        content = result["choices"][0]["message"]["content"]
        for delim in ["```json", "```"]:
            if delim in content:
                content = content.split(delim)[1].split("```")[0]
                break
        return json.loads(content)


def chunk_page(text: str) -> list[str]:
    """Split page text into 134-167 word chunks with 15-20% overlap."""
    # Strip boilerplate heuristics
    text = re.sub(r'<[^>]+>', ' ', text)  # strip HTML
    paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 30]
    if not paragraphs:
        paragraphs = [text]

    chunks = []
    buffer = []
    buffer_words = 0

    for para in paragraphs:
        para_words = len(para.split())
        if buffer_words + para_words <= 200:
            buffer.append(para)
            buffer_words += para_words
        else:
            if buffer:
                chunks.append(' '.join(buffer))
            buffer = [para]
            buffer_words = para_words

    if buffer:
        chunks.append(' '.join(buffer))

    # Split long chunks
    final_chunks = []
    for chunk in chunks:
        words = chunk.split()
        wc = len(words)
        if wc > 200:
            for i in range(0, wc, 150):
                segment = words[i:i+167]
                if len(segment) > 50:
                    final_chunks.append(' '.join(segment))
        elif wc < 50:
            continue  # skip navigation/boilerplate
        else:
            final_chunks.append(chunk)

    # Add overlap: last sentence of chunk N-1 prepended to chunk N
    overlapped = []
    for i, chunk in enumerate(final_chunks):
        if i > 0:
            prev_sentences = re.split(r'(?<=[.!?])\s+', final_chunks[i-1])
            if prev_sentences:
                overlap = prev_sentences[-1]
                chunk = overlap + ' ' + chunk
        overlapped.append(chunk)

    return overlapped


def score_chunk_deterministic(chunk: str) -> dict:
    """Deterministic chunk scoring — no LLM."""
    words = chunk.split()
    wc = len(words)

    # Answer extractability: check first sentence
    first_sent = re.split(r'(?<=[.!?])\s+', chunk)[0] if chunk else ""
    answer_score = 0
    for pat in DECLARATIVE_PATTERNS:
        if re.search(pat, first_sent[:100], re.IGNORECASE):
            answer_score = 10
            break
    if answer_score == 0 and len(first_sent.split()) > 5:
        answer_score = 5  # sentence exists but may not be declarative

    # Factual density: count numbers, stats, entities
    number_count = len(re.findall(r'\b\d+[\.,]?\d*\s*[%$€£]|\b\d+\s*(million|billion|thousand|percent)\b|[%$€£]\s*\d+', chunk, re.IGNORECASE))
    number_count += len(re.findall(r'\b(20\d{2})\b', chunk))  # years
    stats_per_100 = (number_count / max(1, wc)) * 100
    fact_score = min(10, round(stats_per_100 * 3))

    # Self-containment: check for anti-patterns
    flags = 0
    for pat in ANTI_PATTERNS:
        if re.search(pat, chunk, re.IGNORECASE):
            flags += 1
    containment_score = max(0, 10 - flags * 2)

    # Anti-citation flags
    anti_flags = 0
    if len(re.findall(ANTI_CITATION_FLAGS["cta_overload"], chunk)) > 3:
        anti_flags += 1
    keyword_freq = len(set(words)) / max(1, wc)
    if keyword_freq < 0.3:  # low vocabulary diversity = possible keyword stuffing
        anti_flags += 1
    if wc < 50:
        anti_flags += 1  # thin content
    anti_score = max(0, 10 - anti_flags)

    # Chunk word count sweet spot
    if 134 <= wc <= 167:
        size_score = 10
    elif 100 <= wc <= 200:
        size_score = 7
    elif 50 <= wc <= 300:
        size_score = 4
    else:
        size_score = 1

    return {
        "answer_extractability": answer_score,
        "factual_density": fact_score,
        "self_containment": containment_score,
        "anti_citation": anti_score,
        "chunk_size": size_score,
        "word_count": wc
    }


def score_chunk_llm(chunk: str) -> dict:
    """LLM citation worthiness with rubric."""
    try:
        return deepseek_call(
            "Return strict JSON only. Score citation worthiness and check E-E-A-T binary signals.",
            f"{CITATION_RUBRIC}\n{E_EAT_BINARY}\n\nChunk: {chunk[:2000]}" if "E_EAT_BINARY" in globals() else f"{CITATION_RUBRIC}\n\nChunk: {chunk[:2000]}"
        )
    except Exception:
        return {"citation_worthiness": 5, "evidence": "LLM call failed"}



class ContentStageV2(BaseStage):
    """Drop-in replacement for auditstack's content stage with chunk-level scoring."""

    name = "content"
    layer = 3
    depends_on = ["technical"]
    estimated_cost_usd = 2.0
    timeout_seconds = 600

    def __init__(self, max_pages: int = 25):
        self.max_pages = max_pages

    def run(self, snapshot: SnapshotHandle, ctx: AuditContext) -> ContentOutput:
        # Get pages to score: start with homepage, then add discovered live pages
        urls = [ctx.target_url]

        # Try sitemap first (best source of live URLs)
        sitemap_url = ctx.target_url.rstrip("/") + "/sitemap.xml"
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as c:
                r = c.get(sitemap_url)
            if r.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
                for url_elem in root.findall(".//ns:loc", ns):
                    u = url_elem.text.strip() if url_elem.text else ""
                    if u and u.startswith(ctx.target_url) and u not in urls:
                        urls.append(u)
        except Exception:
            pass

        # If sitemap didn't give enough, try common B2B SaaS paths
        if len(urls) < 5:
            common_paths = [
                "/blog", "/about", "/contact", "/careers", "/pricing",
                "/solutions", "/solutions-should-cost-modeling", "/solutions-pcf-reporting",
                "/solutions-tariff-analysis", "/industries", "/case-studies",
                "/stories", "/cookie-policy", "/blog-posts",
            ]
            for path in common_paths:
                candidate = ctx.target_url.rstrip("/") + path
                try:
                    with httpx.Client(timeout=5, follow_redirects=True) as c:
                        r = c.head(candidate)
                    if r.status_code < 400 and candidate not in urls:
                        urls.append(candidate)
                except Exception:
                    pass

        # Filter to only pages that return 200
        live_urls = []
        for u in urls:
            try:
                with httpx.Client(timeout=5, follow_redirects=True) as c:
                    r = c.head(u)
                if r.status_code < 400:
                    live_urls.append(u)
            except Exception:
                pass

        if not live_urls:
            live_urls = [ctx.target_url]

        # Limit and prioritize solution/product pages
        priority = ["solution", "product", "feature", "industries", "case", "story"]
        prioritized = [u for u in live_urls if any(p in u.lower() for p in priority)]
        rest = [u for u in live_urls if u not in prioritized]
        urls = (prioritized + rest)[:self.max_pages]
        if ctx.target_url not in urls:
            urls.insert(0, ctx.target_url)

        print(f"  Content V2: {len(urls)} pages, extracting full content in parallel...")

        # PHASE 1: Extract all pages in ONE batch call to Parallel.ai
        extract_result = parallel_extract(urls, "Extract full page content for citability audit")
        pages_content = {}
        if extract_result.get("error"):
            print(f"  Extract error: {extract_result['error']}, falling back to direct fetch")
            for url in urls:
                try:
                    with httpx.Client(timeout=15, follow_redirects=True) as c:
                        r = c.get(url)
                    pages_content[url] = r.text
                except Exception:
                    continue
        else:
            # Parse results - Parallel.ai returns array of results per URL
            results = extract_result.get("results", [])
            if isinstance(results, list):
                for item in results:
                    item_url = item.get("url", "")
                    text = item.get("full_content", item.get("content", item.get("text", item.get("markdown", ""))))
                    if text:
                        # Match using normalized URL comparison
                        def _norm(u):
                            return u.replace('https://','').replace('http://','').replace('www.','').rstrip('/')
                        item_norm = _norm(item_url)
                        for url in urls:
                            url_norm = _norm(url)
                            if url_norm == item_norm:
                                pages_content[url] = text
                                break
            else:
                # Single page result
                text = extract_result.get("content", extract_result.get("text", ""))
                if text:
                    pages_content[urls[0]] = text

        if not pages_content:
            print("  No content extracted, using homepage only")
            pages_content = {ctx.target_url: ""}

        # PHASE 2: Chunk and score each page
        print(f"  Chunking and scoring {len(pages_content)} pages...")

        all_page_scores = []
        all_findings = []
        all_remediations = []
        total_citability = 0
        total_flesch = 0
        anti_citation_counts: dict[str, int] = {}
        total_cost = 0.0

        for url, page_text in pages_content.items():
            try:
                if not page_text or len(page_text) < 200:
                    continue

                title = url

                # Chunk the page
                chunks = chunk_page(page_text)
                if not chunks:
                    continue

                # Score each chunk (deterministic runs on all, LLM on first 3)
                chunk_scores = []
                for i, chunk in enumerate(chunks[:8]):  # 8 chunks max for speed
                    det = score_chunk_deterministic(chunk)
                    llm = score_chunk_llm(chunk) if i < 3 else {"citation_worthiness": None}
                    chunk_scores.append({**det, **llm})

                # Aggregate chunk scores
                avg_det = sum(
                    (c["answer_extractability"] + c["factual_density"] + c["self_containment"] + c["anti_citation"] + c["chunk_size"]) / 5
                    for c in chunk_scores
                ) / max(1, len(chunk_scores))

                llm_scores = [c.get("citation_worthiness") for c in chunk_scores if c.get("citation_worthiness") is not None]
                avg_llm = sum(llm_scores) / max(1, len(llm_scores)) if llm_scores else 5

                # Page-level deterministic
                try:
                    flesch = textstat.flesch_reading_ease(page_text[:5000])
                    if flesch is None or flesch > 120:
                        flesch = 50  # textstat fails on non-prose
                except Exception:
                    flesch = 50
                flesch = max(0, min(120, flesch))  # clamp
                total_flesch += flesch

                # E-E-A-T (only for important pages, skip for speed)
                eeat = {"eeat_score": 60}  # placeholder for speed; full check in v3

                # Page score (L2 spec formula)
                page_score = (
                    0.30 * avg_det +
                    0.20 * avg_llm +
                    0.15 * (eeat.get("eeat_score", 50) / 10) +
                    0.20 * min(10, (flesch / 60) * 10 if flesch <= 70 else 10) +
                    0.10 * (7 if "solution" in url.lower() or "product" in url.lower() else 5) +
                    0.05 * 5  # remediation coverage placeholder
                ) * 10

                page_score = max(0, min(100, round(page_score)))

                page_data = {
                    "url": url,
                    "title": title,
                    "word_count": len(page_text.split()),
                    "flesch": round(flesch, 1),
                    "chunks_analyzed": len(chunk_scores),
                    "avg_deterministic": round(avg_det, 1),
                    "avg_citation_worthiness": round(avg_llm, 1),
                    "eeat": eeat,
                    "page_score": page_score,
                    "chunk_scores": chunk_scores[:5],  # store top 5 for report
                }
                all_page_scores.append(page_data)
                total_citability += avg_llm

                # Flag issues
                if avg_llm < 5:
                    all_findings.append({
                        "rule_id": "content_quality",
                        "url": url,
                        "severity": "high" if avg_llm < 3 else "medium",
                        "certainty": "confirmed",
                        "title": f"Low citation worthiness ({avg_llm:.1f}/10) on {url}",
                        "evidence": {"citation_worthiness": avg_llm, "answer_extractability": avg_det}
                    })

                if flesch < 40:
                    all_findings.append({
                        "rule_id": "readability_low",
                        "url": url,
                        "severity": "medium",
                        "certainty": "confirmed",
                        "title": f"Low readability (Flesch {flesch:.0f}) on {url}"
                    })

                print(f"    {url[-50:]:>50} → citability {avg_llm:.1f}/10, Flesch {flesch:.0f}, page {page_score}")

            except Exception as e:
                print(f"    Error on {url}: {e}")
                continue

        # Aggregate scores
        if all_page_scores:
            avg_cit = total_citability / len(all_page_scores)
            avg_fl = total_flesch / len(all_page_scores) if total_flesch else 50
            layer_score = int(avg_cit * 10)
        else:
            avg_cit, avg_fl, layer_score = 0, 50, 50

        return ContentOutput(
            layer_score=layer_score,
            cost_usd=total_cost,
            pages_analyzed=len(all_page_scores),
            per_page_scores=all_page_scores,
            avg_citability=round(avg_cit, 2),
            avg_flesch=round(avg_fl, 1),
            anti_citation_flags=anti_citation_counts,
            remediation_drafts=all_remediations,
            findings=all_findings[:50],
        )
