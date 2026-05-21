"""
Layer 3 Stage — External Presence audit as an auditstack pipeline stage.
Uses parallel Parallel.ai Search + Extract for speed.

Registers as 'external_presence' stage, depends_on=['technical'].
"""

from __future__ import annotations
import json, os, re, urllib.request, urllib.error, concurrent.futures
from typing import Any

from auditstack.context import AuditContext
from auditstack.schemas.stage_outputs import StageOutput
from auditstack.snapshot import SnapshotHandle
from auditstack.stages.base import BaseStage

PARALLEL_KEY = os.environ.get("PARALLEL_KEY", "KtepRKsixtAmtjSnaUP-U3wxmqLKiM3gkC_Q9YAW")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

# ── Platform definitions ──────────────────────────────────────────
PLATFORMS = {
    "G2": {
        "search": "Find Muir AI G2 profile: reviews, rating, category",
        "queries": ['"Muir AI" G2 reviews profile', 'site:g2.com "Muir AI"'],
    },
    "Capterra": {
        "search": "Find Muir AI Capterra profile: reviews, rating",
        "queries": ['"Muir AI" Capterra software', 'site:capterra.com "Muir AI"'],
    },
    "LinkedIn": {
        "search": "Find Muir AI LinkedIn company page: description, followers, posts",
        "queries": ['Muir AI LinkedIn company page', 'site:linkedin.com/company "Muir AI"'],
    },
    "YouTube": {
        "search": "Find Muir AI YouTube channel or third-party video mentions",
        "queries": ['"Muir AI" YouTube channel', 'site:youtube.com "Muir AI"'],
    },
    "Reddit": {
        "search": "Find Muir AI mentioned on Reddit: manufacturing, supply chain, cost estimation",
        "queries": ['"Muir AI" Reddit manufacturing', 'site:reddit.com "Muir AI"'],
    },
    "Podcasts": {
        "search": "Find Muir AI podcast guest appearances: founder interviews, industry shows",
        "queries": ['"Muir AI" podcast guest appearance', '"Harris Chalat" podcast'],
    },
    "Publications": {
        "search": "Find Muir AI mentioned in industry publications: TechCrunch, supply chain press",
        "queries": ['"Muir AI" TechCrunch manufacturing', '"Muir AI" industry publication supply chain'],
    },
    "Wikipedia": {
        "search": "Find Muir AI Wikipedia page or Wikidata entity",
        "queries": ['Muir AI Wikipedia', 'site:en.wikipedia.org "Muir AI"'],
    },
}

ICP_CONTEXT = "B2B SaaS. Should-cost modeling, tariff analysis, and product carbon footprint intelligence for manufacturers and supply chain teams at mid-market to enterprise companies (100+ employees, $20M+ revenue). ICP cares about cost reduction, tariff mitigation, and supply chain resilience. Competes with aPriori and Galorath."

RUBRIC = """=== LINKEDIN BENCHMARKS ===
Median B2B followers: 4,500 (Databox, 440 orgs). Good: 5K-25K. Optimal posting: 2-3/week.
Profile completeness: logo, description with ICP keywords, website link, employee count.
Description must include: what company does, who it serves, ICP keywords.
Personal profiles drive 561% more reach than company page.
IMPROVES: AI visibility, branded search, outbound acceptance, retargeting pool.

=== G2 BENCHMARKS ===
10 reviews = Grid minimum. 50 reviews = competitive. 100+ = strong. 4.5+ stars = trust threshold.
100% of ChatGPT-cited tools have G2. Category must match ICP.
IMPROVES: AI citation gate, buyer trust, demo conversion, outbound reply rate.

=== CAPTERRA BENCHMARKS ===
50+ reviews = competitive. 4.5+ stars = good. 99% of ChatGPT-cited tools have Capterra.
Category alignment critical. IMPROVES: same as G2.

=== YOUTUBE BENCHMARKS ===
YouTube mentions = strongest AI signal (0.737 correlation, Ahrefs Dec 2025).
10+ videos with human-reviewed transcripts = good. 29.5% of Google AI Overviews cite YouTube.
IMPROVES: AI citation (#1 signal), Google AI Overviews, organic search.

=== REDDIT BENCHMARKS ===
46.7% of Perplexity citations. 11.3% of ChatGPT citations. 3-5 relevant subreddits.
Must be genuinely helpful, not promotional. IMPROVES: AI citation, corroboration, branded search.

=== PODCASTS BENCHMARKS ===
2-4 appearances/month = sustainable founder pace. Transcripts = AI fuel (5K-15K words/episode).
60-90 day lag for AI indexing. IMPROVES: AI citation, backlinks, domain authority.

=== PUBLICATIONS BENCHMARKS ===
2-4 contributed articles/year on DR 40+ sites = good. 96% of AI citations from third-party.
IMPROVES: AI citation, domain authority, branded search.

=== WIKIPEDIA BENCHMARKS ===
Page exists = 10/10. Wikidata entity = 5/10. Neither = 0. Cannot be created by company.
IMPROVES: AI entity recognition, Knowledge Panel, trust signals."""

SCORING_PROMPT = """Brand: {brand}
ICP: {icp}
Competitors: {competitors}
{RUBRIC}

=== RESEARCH DATA ===
{research}

Score each platform 0-10 using the benchmarks. For each platform provide:
- score: 0-10
- evidence: what was found
- icp_alignment: aligned/partial/misaligned/no_content
- currently_improves: what this is contributing right now
- missed_opportunity: what fixing this would unlock
- recommendation: one specific action

Return JSON:
{{"layer_score": 0-100, "platforms": {{"Platform": {{...}}}}, "top_3_gaps": ["..."], "summary": "one paragraph"}}"""

class ExternalPresenceOutput(StageOutput):
    layer_score: int | None = None
    platforms: dict[str, Any] = {}
    top_gaps: list[str] = []
    summary: str = ""


def _parallel_search(platform_def: dict) -> dict:
    """Single platform search."""
    req = urllib.request.Request(
        "https://api.parallel.ai/v1beta/search",
        data=json.dumps({"objective": platform_def["search"], "queries": platform_def["queries"], "mode": "fast"}).encode(),
        headers={"x-api-key": PARALLEL_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def _llm_score(prompt: str) -> dict:
    """Single LLM call to score all platforms."""
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Audit external presence. Return strict JSON only."},
                {"role": "user", "content": prompt[:25000]}
            ], "temperature": 0.3, "max_tokens": 3000
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


class ExternalPresenceStage(BaseStage):
    name = "external_presence"
    layer = 3  # sits between content (layer 2/3) and ai_retrieval (layer 5) in our framework
    depends_on = ["technical"]
    estimated_cost_usd = 0.50
    timeout_seconds = 120

    def run(self, snapshot: SnapshotHandle, ctx: AuditContext) -> ExternalPresenceOutput:
        brand = ctx.client_name or "the brand"
        competitors = ", ".join(ctx.competitors) if ctx.competitors else "none specified"

        # === PHASE 1: Search all 8 platforms in PARALLEL ===
        print(f"  L3: Searching {len(PLATFORMS)} platforms in parallel...")
        research = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = {ex.submit(_parallel_search, pdef): name for name, pdef in PLATFORMS.items()}
            for fut in concurrent.futures.as_completed(futures):
                name = futures[fut]
                try:
                    result = fut.result()
                    research.append(f"\n--- {name} ---\n{json.dumps(result, indent=2)[:2000]}")
                except Exception as e:
                    research.append(f"\n--- {name} ---\nError: {e}")

        # === PHASE 2: LLM scoring ===
        print(f"  L3: Scoring with benchmarks...")
        prompt = SCORING_PROMPT.format(
            brand=brand, icp=ICP_CONTEXT, competitors=competitors,
            RUBRIC=RUBRIC, research="\n".join(research)
        )
        try:
            scores = _llm_score(prompt)
        except Exception as e:
            scores = {"layer_score": 30, "platforms": {}, "top_3_gaps": [str(e)], "summary": "Scoring failed"}

        return ExternalPresenceOutput(
            layer_score=scores.get("layer_score", 0),
            cost_usd=0.0,
            platforms=scores.get("platforms", {}),
            top_gaps=scores.get("top_3_gaps", []),
            summary=scores.get("summary", ""),
        )
