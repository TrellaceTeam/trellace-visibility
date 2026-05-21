"""
Per-page data enrichment for all L1+L2 checks.
Runs on every crawled page, not just homepage.
"""
import json, os, re, urllib.request, urllib.error, time
import httpx

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

def norm_url(u):
    return u.replace("https://","").replace("http://","").replace("www.","").rstrip("/")

def check_page(url: str) -> dict:
    """Run all L1+L2 per-page checks on one URL. Returns dict of results."""
    result = {"url": url, "ok": False, "status": 0, "error": None}
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as c:
            r = c.get(url)
        result["status"] = r.status_code
        if r.status_code >= 400:
            result["error"] = f"HTTP {r.status_code}"
            return result
        html = r.text
        headers = dict(r.headers)
        result["ok"] = True
    except Exception as e:
        result["error"] = str(e)
        return result

    # ── L1 A: Binary gates (per-page) ──
    # Canonical URL
    result["has_canonical"] = "canonical" in html[:10000].lower() or 'rel="canonical"' in html[:10000]
    # Breadcrumb
    result["has_breadcrumb"] = "BreadcrumbList" in html or 'breadcrumb' in html.lower()
    # Schema types on this page
    try:
        from auditstack.tools.schema_validator import validate_html
        vr = validate_html(html)
        result["schema_types"] = vr.types_found
        result["schema_issues"] = len(vr.issues)
    except Exception:
        result["schema_types"] = []
        result["schema_issues"] = 0

    # ── L1 B: Scalar (per-page) ──
    # Cache
    result["cache_control"] = headers.get("Cache-Control", headers.get("cache-control", ""))
    result["has_caching"] = bool(result["cache_control"])
    # TTFB (rough)
    result["ttfb_ms"] = r.elapsed.total_seconds() * 1000 if hasattr(r, "elapsed") else None

    # ── L2 A: Binary gates (per-page, no LLM) ──
    # Author bio
    has_author = bool(re.search(r'(?i)(?:author|byline|written by|published by)', html[:5000]))
    has_author_meta = bool(re.search(r'(?i)<meta[^>]*name\s*=\s*["\']author["\'][^>]*content', html[:5000]))
    result["has_author"] = has_author or has_author_meta

    # Credentials
    result["has_credentials"] = bool(re.search(r'(?i)(?:phd|professor|engineer|specialist|expert|years of experience|formerly|ex-|founder|ceo|cto)', html[:8000]))

    # Last-updated date
    result["has_last_updated"] = bool(re.search(r'(?i)(?:last updated|updated on|published|modified|date)', html[:5000]))

    # Contact
    result["has_contact"] = bool(re.search(r'(?i)(?:contact|email|@|phone|call us|get in touch|reach out)', html[:5000]))

    # External sources cited
    result["has_external_sources"] = bool(re.search(r'(?i)(?:source|reference|citation|according to|study by|report by|research from)', html[:8000]))

    # Original data
    result["has_original_data"] = bool(re.search(r'(?i)(?:we (?:surveyed|analyzed|tested|measured|found|tracked|processed)|our (?:data|research|analysis|study|survey|benchmark))', html[:8000]))
    # Heading hierarchy
    h1s = len(re.findall(r'(?i)<h1[^>]*>', html))
    h2s = len(re.findall(r'(?i)<h2[^>]*>', html))
    h3s = len(re.findall(r'(?i)<h3[^>]*>', html))
    result["h1_count"] = h1s
    result["h2_count"] = h2s
    result["h3_count"] = h3s
    result["has_headings"] = h1s > 0 and h2s > 0
    result["single_h1"] = h1s == 1

    # Lists
    uls = len(re.findall(r'(?i)<ul[^>]*>', html))
    ols = len(re.findall(r'(?i)<ol[^>]*>', html))
    result["has_lists"] = (uls + ols) > 0

    # FAQ detection
    faq_found = False
    faq_text = ""
    for pat in [r'(?i)<h[23][^>]*>\s*(?:frequently\s+asked\s+questions?|faq|common\s+questions?)\s*</h[23]>',
                r'(?i)FAQPage', r'(?i)"@type"\s*:\s*"FAQPage"']:
        if re.search(pat, html):
            faq_found = True; break
    if faq_found:
        faq_text = ""
        # Strategy 1: find FAQ heading and extract content until next H2/H3
        faq_heading = re.search(r'(?i)<(h[234])[^>]*>\s*(?:frequently\s+asked\s+questions?|faq|common\s+questions?|questions?\s*(?:&|and)\s*answers?)\s*</\1>', html)
        if faq_heading:
            start = faq_heading.end()
            # Find next major heading or section end
            end_match = re.search(r'(?i)<(?:h[23]|section|footer)', html[start:start+5000])
            end = start + end_match.start() if end_match else min(start+5000, len(html))
            faq_text = html[start:end]
        # Strategy 2: extract FAQ from JSON-LD schema
        if not faq_text and 'FAQPage' in html:
            # Find JSON-LD blocks with FAQ data
            ld_blocks = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
            for ld in ld_blocks:
                if 'FAQPage' in ld:
                    # Extract question-answer pairs from schema
                    qas = re.findall(r'"name"\s*:\s*"([^"]+)"\s*,\s*"acceptedAnswer"[^}]*"text"\s*:\s*"([^"]+)"', ld, re.DOTALL)
                    if qas:
                        faq_text = " ".join(f"Q: {q} A: {a}" for q, a in qas[:5])
                        break
        # Strategy 3: look for question-like H3s with following content
        if not faq_text:
            qa_pairs = re.findall(r'(?i)<h3[^>]*>(.{10,100}?\?)</h3>(.{50,500}?)(?=<h[23]|$)', html, re.DOTALL)
            if qa_pairs:
                faq_text = " ".join(f"Q: {re.sub(r'<[^>]+>',' ',q).strip()} A: {re.sub(r'<[^>]+>',' ',a).strip()}" for q,a in qa_pairs[:5])
        # Clean
        faq_text = re.sub(r'<[^>]+>', ' ', faq_text)
        faq_text = re.sub(r'\s+', ' ', faq_text).strip()[:1500]
    result["has_faq"] = faq_found
    result["faq_text"] = faq_text

    # Case studies
    result["has_case_study"] = bool(re.search(r'case.stud|case\s+study|customer.story|success.story', html, re.IGNORECASE))

    # ── L2 B: Scalar (per-page) ──
    # Image presence (for alt text check via Lighthouse proxy)
    img_count = len(re.findall(r'(?i)<img[^>]*>', html))
    result["image_count"] = img_count
    result["images_with_alt"] = len(re.findall(r'(?i)<img[^>]*alt\s*=\s*"[^"]', html))

    return result


def check_llms_txt(base_url: str) -> dict:
    url = base_url.rstrip("/") + "/llms.txt"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as r:
            content = r.read().decode("utf-8", errors="ignore")
        lines = [l for l in content.split("\n") if l.strip() and not l.startswith("#")]
        has_h1 = any(l.strip().startswith("# ") for l in content.split("\n"))
        return {"exists": True, "size_bytes": len(content), "lines": len(lines),
                "has_h1": has_h1, "preview": content[:300]}
    except Exception:
        return {"exists": False}


def score_eeat(page_text: str) -> dict:
    """Full 20-item E-E-A-T rubric (was disabled for speed, now enabled)."""
    if not page_text or len(page_text) < 200:
        return {"eeat_score": 0, "blocked": True, "veto_failures": ["thin_content"]}
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Return strict JSON only."},
                    {"role": "user", "content": f"""Score this page on E-E-A-T. Each item: Pass=10, Partial=5, Fail=0.
EXPERIENCE: E1-first_person_evidence, E2-original_data, E3-practical_application, E4-limitations_stated, E5-audience_specific
EXPERTISE: Ep1-technical_accuracy, Ep2-depth, Ep3-current_knowledge, Ep4-credentials_visible, Ep5-appropriate_complexity
AUTHORITY: A1-external_sources_cited, A2-industry_recognition, A3-backlink_profile, A4-brand_recognition, A5-comparative_context
TRUST: T1-contact_accessible, T2-editorial_transparency, T3-factual_claims_sourced, T4-no_deceptive_patterns, T5-accuracy_signals
VETO: If T3 or T4 fails → score capped at 50, marked UNRELIABLE. Two vetoes → BLOCKED (0).

Page: {page_text[:6000]}
Return: {{"items": {{"E1": 10, ...}}, "veto_failures": [], "eeat_score": 75, "blocked": false, "top_finding": "one sentence"}}"""}
            ], "temperature": 0.3, "max_tokens": 600
            }).encode(),
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            for delim in ["```json", "```"]:
                if delim in content: content = content.split(delim)[1].split("```")[0]; break
            return json.loads(content)
    except Exception as e:
        return {"eeat_score": 50, "blocked": False, "veto_failures": [], "top_finding": f"LLM failed: {e}"}


def score_faq_quality(faq_text: str) -> dict:
    if not faq_text or len(faq_text) < 50:
        return {"score": 0, "evidence": "No FAQ content"}
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": "Return JSON."},
                             {"role": "user", "content": f"Score FAQ 0-10: relevance(0-3), answer_quality(0-3), structure(0-2), uniqueness(0-2).\nFAQ: {faq_text[:1500]}\nReturn: {{\"score\": 7, \"evidence\": \"one sentence\"}}"}],
                "temperature": 0.3, "max_tokens": 200
            }).encode(),
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            for delim in ["```json", "```"]:
                if delim in content: content = content.split(delim)[1].split("```")[0]; break
            return json.loads(content)
    except Exception as e:
        return {"score": 0, "evidence": f"Failed: {e}"}


def enrich_all(base_url: str, page_urls: list) -> dict:
    """Run all per-page enrichment checks."""
    enrichment = {}
    enrichment["llms_txt"] = check_llms_txt(base_url)

    # Per-page checks
    enrichment["pages"] = {}
    for url in page_urls[:15]:
        result = check_page(url)
        enrichment["pages"][norm_url(url)] = result

    # FAQ quality for pages that have FAQ
    enrichment["faq_quality"] = {}
    for normed, data in enrichment["pages"].items():
        if data.get("has_faq") and data.get("faq_text"):
            enrichment["faq_quality"][normed] = score_faq_quality(data["faq_text"])

    # E-E-A-T for important pages
    enrichment["eeat"] = {}
    priority = ["solution", "product", "industries", "about", "pricing"]
    important = [u for u in page_urls if any(p in u.lower() for p in priority)]
    for url in (important[:5] or page_urls[:3]):
        try:
            with httpx.Client(timeout=10, follow_redirects=True) as c:
                r = c.get(url)
            enrichment["eeat"][norm_url(url)] = score_eeat(r.text[:8000])
        except Exception:
            pass

    # Aggregate summaries
    enrichment["summary"] = _build_summary(enrichment)
    return enrichment


def _build_summary( enrichment: dict) -> dict:
    """Aggregate per-page checks into summary stats."""
    pages = enrichment.get("pages", {})
    total = len(pages)
    if total == 0: return {}

    def _pct(field):
        return sum(1 for p in pages.values() if p.get(field)) / total

    def _avg(field):
        vals = [p.get(field) for p in pages.values() if p.get(field) is not None]
        return sum(vals)/len(vals) if vals else 0

    def _sum(field):
        return sum(p.get(field, 0) for p in pages.values())

    schema_counts = {}
    for p in pages.values():
        for t in p.get("schema_types", []):
            schema_counts[t] = schema_counts.get(t, 0) + 1

    pages_with_schema = sum(1 for p in pages.values() if p.get("schema_types"))
    pages_with_faq = sum(1 for p in pages.values() if p.get("has_faq"))

    return {
        "total_pages": total,
        "has_canonical_pct": _pct("has_canonical"),
        "has_breadcrumb_pct": _pct("has_breadcrumb"),
        "has_caching_pct": _pct("has_caching"),
        "has_headings_pct": _pct("has_headings"),
        "single_h1_pct": _pct("single_h1"),
        "has_lists_pct": _pct("has_lists"),
        "has_faq_pct": _pct("has_faq"),
        "has_case_study_pct": _pct("has_case_study"),
        "has_author_pct": _pct("has_author"),
        "has_credentials_pct": _pct("has_credentials"),
        "has_last_updated_pct": _pct("has_last_updated"),
        "has_contact_pct": _pct("has_contact"),
        "has_external_sources_pct": _pct("has_external_sources"),
        "has_original_data_pct": _pct("has_original_data"),
        "avg_ttfb_ms": round(_avg("ttfb_ms")),
        "avg_h1": round(_avg("h1_count"), 1),
        "avg_h2": round(_avg("h2_count"), 1),
        "avg_images": round(_avg("image_count")),
        "alt_text_pct": round(_sum("images_with_alt") / max(1, _sum("image_count")), 2),
        "pages_with_schema": pages_with_schema,
        "schema_type_counts": schema_counts,
        "pages_with_faq": pages_with_faq,
    }
