"""
Output enhancements: A/B/C labels, priority ranking, remediation drafts, "what it improves" notes.
Drop-in additions for unified_runner.py's contextualize_output.
"""
import hashlib, json, os, urllib.request, urllib.error

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

# ── A/B/C Classification ──────────────────────────────────────────
# Mapping from rule_id to category
RULE_CATEGORY = {
    # Layer 1
    "broken_link": ("L1", "A", "Binary — page is returning 404. Must fix."),
    "missing_title": ("L1", "A", "Binary — page has no title tag. Must fix."),
    "missing_meta_description": ("L1", "A", "Binary — page has no meta description."),
    "schema_validation": ("L1", "A", "Binary — schema markup has errors."),
    "lcp_slow": ("L1", "B", "Scalar — page load speed. Target < 2.5s."),
    "cls_high": ("L1", "B", "Scalar — layout stability. Target < 0.1."),
    "no_gsc": ("L1", "A", "Binary — Google Search Console not connected."),
    # Layer 2
    "content_quality": ("L2", "B", "Scalar — content citability score. Target 7+/10."),
    "readability_low": ("L2", "B", "Scalar — Flesch score. Target 60-70."),
    # Layer 3
    "no_wikipedia": ("L3", "A", "Binary — Wikipedia page missing. Cannot create directly."),
    "missing_linkedin": ("L3", "A", "Binary — LinkedIn company page missing."),
    # Layer 4
    "low_sov": ("L4", "B", "Scalar — Share of Voice on AI platforms."),
    "sharp_layer_drop": ("L4", "B", "Scalar — Score dropped vs previous audit."),
}

# ── What each finding improves ─────────────────────────────────────
WHAT_IMPROVES = {
    "broken_link": "Google ranking, crawl budget, user experience",
    "missing_title": "Google ranking, organic CTR",
    "schema_validation": "Rich snippets, AI content parsing, Knowledge Panel eligibility",
    "lcp_slow": "Google ranking, Quality Score (lower CPC), user bounce rate",
    "cls_high": "Google ranking, Quality Score, user experience",
    "no_gsc": "Indexation monitoring, search query visibility",
    "content_quality": "AI citation rate, Google organic traffic, conversion rate",
    "readability_low": "User engagement, AI extraction accuracy, time on page",
    "no_wikipedia": "AI entity recognition, Knowledge Panel, trust signals",
    "missing_linkedin": "AI visibility, branded search volume, outbound acceptance",
    "low_sov": "AI referral traffic, branded search, discovery calls from AI",
    "sharp_layer_drop": "Regression detection — fixes were lost or site changed",
}

DEFAULT_WHAT_IMPROVES = "Overall visibility score — affects discovery across all channels"


def classify_finding(finding: dict) -> dict:
    """Add A/B/C category, what it improves, and fix guidance."""
    from abc_classifier import classify_and_fix
    # Get fix guidance from ABC classifier
    finding = classify_and_fix(finding)
    # Add what it improves
    rule_id = finding.get("rule_id", "unknown")
    improves = WHAT_IMPROVES.get(rule_id, DEFAULT_WHAT_IMPROVES)
    finding["what_it_improves"] = improves
    return finding


# ── Priority Ranking ───────────────────────────────────────────────
CERTAINTY_NUM = {"confirmed": 5, "likely": 3, "hypothesis": 1}
SEVERITY_LIFT = {"high": 5, "medium": 3, "low": 1}
EFFORT = {
    "broken_link": 1, "missing_title": 1, "missing_meta_description": 1,
    "schema_validation": 2, "content_quality": 2, "lcp_slow": 3,
    "cls_high": 2, "no_gsc": 1, "no_wikipedia": 4, "missing_linkedin": 1,
    "low_sov": 4, "sharp_layer_drop": 1, "readability_low": 2,
}

def finding_id(stage_name: str, url: str, rule_id: str) -> str:
    payload = f"{stage_name}|{url}|{rule_id}".encode()
    return hashlib.sha256(payload).hexdigest()[:16]

def rank_findings(all_findings: list) -> list:
    """Rank all findings by priority = (lift × certainty) / effort."""
    ranked = []
    for f in all_findings:
        severity = f.get("severity", "medium")
        certainty = f.get("certainty", "likely")
        rule_id = f.get("rule_id", "unknown")
        lift = SEVERITY_LIFT.get(severity, 3)
        cert = CERTAINTY_NUM.get(certainty, 3)
        effort = EFFORT.get(rule_id, 3)
        priority = round((lift * cert) / max(1, effort), 2)
        fid = finding_id(f.get("stage_name", ""), f.get("url", ""), rule_id)
        ranked.append({**f, "lift": lift, "effort": effort, "priority": priority, "finding_id": fid})
    ranked.sort(key=lambda r: r["priority"], reverse=True)
    for i, r in enumerate(ranked, 1):
        r["rank"] = i
    return ranked


# ── Remediation Drafts ─────────────────────────────────────────────
REMEDIATION_PROMPT = """You are a content editor. Generate a 30-80 word replacement for this content chunk that fixes the problem described. Preserve the original meaning and facts. Write in an educational tone (not promotional). Use language the target audience (manufacturers and supply chain professionals) would recognize. Do not add facts you cannot verify.

Problem: {problem}
Original chunk: {chunk}

Return JSON: {{"draft": "the fixed text", "explanation": "what was changed and why"}}"""

def generate_remediation(problem: str, chunk: str) -> dict:
    """Generate a remediation draft for a low-scoring content chunk."""
    try:
        req = urllib.request.Request(
            "https://api.deepseek.com/v1/chat/completions",
            data=json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "Return strict JSON only."},
                    {"role": "user", "content": REMEDIATION_PROMPT.format(problem=problem, chunk=chunk[:2000])}
                ], "temperature": 0.3, "max_tokens": 500
            }).encode(),
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            content = result["choices"][0]["message"]["content"]
            for delim in ["```json", "```"]:
                if delim in content:
                    content = content.split(delim)[1].split("```")[0]
                    break
            return json.loads(content)
    except Exception as e:
        return {"draft": "", "explanation": f"Failed: {e}"}


# ── Collect findings from all stages ────────────────────────────────
def collect_all_findings(stages: dict) -> list:
    """Collect findings from all stage outputs, classify, and rank."""
    all_findings = []
    for stage_name, stage_data in stages.items():
        findings = stage_data.get("findings", [])
        for f in findings:
            f["stage_name"] = stage_name
            f = classify_finding(f)
            all_findings.append(f)
    return rank_findings(all_findings)


# ── Summary builder ────────────────────────────────────────────────
def build_output_summary(ctx: dict, all_findings: list, remediation_count: int = 3) -> dict:
    """Add ranked findings, A/B/C summary, and remediation to the contextual output."""
    # A/B/C counts
    a_count = sum(1 for f in all_findings if f.get("category") == "A")
    b_count = sum(1 for f in all_findings if f.get("category") == "B")
    ctx["binary_gates"] = a_count
    ctx["scalar_issues"] = b_count

    # Top 5 ranked findings
    top5 = all_findings[:5]
    ctx["top_findings"] = [{
        "rank": f["rank"],
        "title": f.get("title", ""),
        "layer": f.get("layer", "?"),
        "category": f.get("category", "?"),
        "priority": f["priority"],
        "effort": f.get("effort", 3),
        "what_it_improves": f.get("what_it_improves", ""),
    } for f in top5]

    # Remediation for top content issues
    content_findings = [f for f in all_findings if f.get("stage_name") == "content"][:remediation_count]
    ctx["remediations"] = []
    for f in content_findings:
        chunk = f.get("evidence", {}).get("chunk_text", f.get("title", ""))
        if chunk and len(chunk) > 50:
            draft = generate_remediation(f.get("title", "Low citation worthiness"), chunk)
            ctx["remediations"].append({
                "for": f.get("title", "")[:80],
                "draft": draft.get("draft", ""),
                "explanation": draft.get("explanation", ""),
            })

    return ctx
