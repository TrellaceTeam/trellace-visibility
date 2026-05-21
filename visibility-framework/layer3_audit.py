"""Layer 3 — External Presence Audit v2.
Analyzes content, not just existence. Uses real benchmarks.
Connects each finding to what it improves (AI, trust, search, conversion).
"""

import json, sys, urllib.request, urllib.error, os

PARALLEL_KEY = os.environ.get("PARALLEL_KEY", "KtepRKsixtAmtjSnaUP-U3wxmqLKiM3gkC_Q9YAW")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

ICP_CONTEXT = "Muir AI is a B2B SaaS company providing should-cost modeling, tariff analysis, and product carbon footprint intelligence for manufacturers and supply chain teams at mid-market to enterprise companies (100+ employees, $20M+ revenue). Their ICP cares about cost reduction, tariff mitigation, and supply chain resilience. They compete with aPriori and Galorath."

BENCHMARKS = """
REAL BENCHMARKS (from industry research, 2025-2026):

LinkedIn:
  - Median B2B followers: 4,500 (Databox, 440 orgs)
  - Good follower range: 5,000-25,000
  - Optimal posting: 2-3 posts/week (Socialinsider 2026)
  - Company description must include: what the company does, who it serves, keywords that match ICP search intent
  - Personal profiles (CEO, team) drive 561% more reach than company page (van der Blom 2026)
  - Posts with carousels/PDFs get 7% engagement vs 3-4% for text (Socialinsider)
  - IMPROVES: AI visibility (LinkedIn content indexed by search engines), branded search volume, outbound acceptance rate, retargeting pool size

G2:
  - 10 reviews = minimum for Grid appearance
  - 50 reviews = competitive
  - 100+ reviews = strong
  - Median across 200K products: ~5-10 reviews (most products have very few)
  - Rating 4.5+ = buyer trust threshold
  - Profile completeness matters: screenshots, demo video, pricing, AI-focused keywords
  - Category alignment is critical: being in the WRONG category (e.g., "Sustainability" when you're "Cost Estimation") misleads both buyers and AI
  - 100% of tools cited by ChatGPT have G2 profiles (inclusion gate)
  - IMPROVES: AI citation rate (inclusion gate), buyer trust (social proof), outbound reply rate, demo conversion rate

Capterra:
  - 50+ reviews = competitive
  - Same profile quality rules as G2
  - 99% of tools cited by ChatGPT have Capterra profiles
  - IMPROVES: same as G2

YouTube:
  - YouTube mentions = strongest single correlation with AI visibility (0.737) (Ahrefs 75K brands, Dec 2025)
  - Channel should have: 10+ videos, human-reviewed transcripts (not auto-captions), question-format titles, 3-5 paragraph descriptions
  - 29.5% of Google AI Overviews cite YouTube (BrightEdge Oct 2025)
  - Transcripts are the retrieval surface — LLMs READ transcripts, not watch videos
  - IMPROVES: AI citation rate (#1 signal), Google AI Overviews presence, organic search (YouTube results appear in Google)

Reddit:
  - Reddit is 46.7% of Perplexity citations, 11.3% of ChatGPT citations (2026)
  - AI treats Reddit as "real user sentiment" — authentic discussion, not marketing
  - Genuine helpful participation in 3-5 relevant communities (r/manufacturing, r/supplychain, r/industrialengineering)
  - Cannot be promotional — must be genuinely helpful. AI detects promotional language.
  - IMPROVES: AI citation rate (especially Perplexity), corroboration threshold, branded search

Podcasts:
  - 2-4 appearances/month = sustainable pace for founders (Command Your Brand 2026)
  - Transcripts are the value: 5,000-15,000 words of indexable content per episode, 15-30 brand mentions in context, 7-10 citation surfaces per episode
  - AI visibility lag: 60-90 days after recording for transcript indexing
  - IMPROVES: AI citation rate, branded search, backlink profile (show notes link to site), domain authority

Industry Publications:
  - 2-4 contributed articles/year on DR 40+ sites = good
  - Earned coverage (TechCrunch, industry press) builds domain authority
  - 96% of AI citations come from third-party sources, not brand-owned domains
  - IMPROVES: AI citation rate, domain authority, branded search, direct referral traffic

Wikipedia:
  - Wikipedia page = massive AI entity recognition boost
  - Wikidata entity = partial credit
  - Cannot be created by the company — must be earned through notability
  - IMPROVES: AI entity recognition, Knowledge Panel, trust signals
"""

SCORING_PROMPT = """You are auditing a B2B SaaS company's external presence for AI visibility, buyer trust, and search discoverability.

Company: {brand}
ICP context: {icp}

Research data from live searches:
{research}

{benchmarks}

For each platform, provide:
1. A score 0-10 using the benchmarks above
2. What evidence you found (be specific — what content exists, what's missing)
3. Content analysis: is the existing content aligned with the ICP? Does it mention the right keywords? Is the positioning correct or outdated?
4. What this platform currently improves for the brand (based on what exists)
5. What it WOULD improve if fixed (the missed opportunity)
6. A specific, actionable recommendation (one sentence on what to do)

Return JSON:
{{
  "layer_score": 0-100,
  "platforms": {{
    "Platform Name": {{
      "score": 0-10,
      "evidence": "what was found",
      "content_alignment": "ICP-aligned / partially aligned / misaligned / no content",
      "currently_improves": "what this is currently contributing",
      "missed_opportunity": "what fixing this would unlock",
      "recommendation": "specific action to take"
    }}
  }},
  "top_3_gaps": ["gap 1", "gap 2", "gap 3"],
  "summary": "one paragraph assessment"
}}"""


def parallel_search(objective, queries, mode="fast"):
    req = urllib.request.Request(
        "https://api.parallel.ai/v1beta/search",
        data=json.dumps({"objective": objective, "queries": queries, "mode": mode}).encode(),
        headers={"x-api-key": PARALLEL_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def parallel_extract(urls, objective):
    req = urllib.request.Request(
        "https://api.parallel.ai/v1beta/extract",
        data=json.dumps({"urls": urls, "objective": objective, "excerpts": True, "full_content": False}).encode(),
        headers={"x-api-key": PARALLEL_KEY, "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}

def deepseek_analyze(prompt_text):
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps({
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "You audit B2B SaaS external presence. Return strict JSON only."},
                {"role": "user", "content": prompt_text[:25000]}
            ], "temperature": 0.3, "max_tokens": 4000
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


def main():
    brand = sys.argv[1] if len(sys.argv) > 1 else "Muir AI"
    print(f"\n{'='*60}")
    print(f"  LAYER 3 — External Presence Audit: {brand}")
    print(f"{'='*60}\n")

    # Phase 1: Search + Extract content from each platform
    platforms = {
        "LinkedIn": {
            "search_obj": f"Is {brand} on LinkedIn? Find company page, description, employee count, recent posts",
            "queries": [f"{brand} LinkedIn company page", f"site:linkedin.com/company {brand}"],
            "extract_urls": [f"https://www.linkedin.com/company/{brand.lower().replace(' ', '-')}"]
        },
        "G2": {
            "search_obj": f"Does {brand} have a G2 profile? Find reviews, rating, category",
            "queries": [f'"{brand}" G2 reviews', f"site:g2.com {brand}"],
            "extract_urls": []
        },
        "Capterra": {
            "search_obj": f"Does {brand} have a Capterra profile? Find reviews, rating, category",
            "queries": [f'"{brand}" Capterra', f"site:capterra.com {brand}"],
            "extract_urls": []
        },
        "YouTube": {
            "search_obj": f"Does {brand} have a YouTube channel or third-party video mentions?",
            "queries": [f"{brand} YouTube", f"site:youtube.com {brand}"],
            "extract_urls": []
        },
        "Reddit": {
            "search_obj": f"Is {brand} discussed on Reddit? Find mentions in relevant communities",
            "queries": [f"{brand} Reddit manufacturing supply chain", f"site:reddit.com {brand}"],
            "extract_urls": []
        },
        "Podcasts": {
            "search_obj": f"Has {brand} appeared on podcasts? Find episodes, topics, transcripts",
            "queries": [f'"{brand}" podcast guest', f"{brand} podcast appearance"],
            "extract_urls": []
        },
        "Publications": {
            "search_obj": f"Is {brand} mentioned in industry publications? Find articles, press coverage",
            "queries": [f'"{brand}" industry publication', f"{brand} manufacturing supply chain article"],
            "extract_urls": []
        },
        "Wikipedia": {
            "search_obj": f"Does {brand} have a Wikipedia page or Wikidata entity?",
            "queries": [f"{brand} Wikipedia", f"site:en.wikipedia.org {brand}"],
            "extract_urls": []
        },
    }

    research_data = []
    for name, cfg in platforms.items():
        print(f"  Searching {name}...", end=" ", flush=True)
        result = parallel_search(cfg["search_obj"], cfg["queries"])
        research_data.append(f"\n--- {name} SEARCH ---")
        if result.get("error"):
            research_data.append(f"Search error: {result['error']}")
            print("(search failed)")
        else:
            preview = json.dumps(result, indent=2)[:800]
            research_data.append(preview)
            print(f"found {len(result.get('results',[]))} results")

        # Extract content from key URLs if found
        if cfg["extract_urls"]:
            extract = parallel_extract(cfg["extract_urls"], cfg["search_obj"])
            research_data.append(f"\n--- {name} CONTENT ---")
            if extract.get("error"):
                research_data.append(f"Extract error: {extract['error']}")
            else:
                research_data.append(json.dumps(extract, indent=2)[:2000])

    # Phase 2: LLM scoring with benchmarks + content analysis + recommendations
    print("\n  Analyzing with benchmarks...\n")
    research = "\n".join(research_data)
    prompt = SCORING_PROMPT.format(brand=brand, icp=ICP_CONTEXT, research=research, benchmarks=BENCHMARKS)

    try:
        scores = deepseek_analyze(prompt)

        print(f"{'='*60}")
        print(f"  LAYER 3 SCORE: {scores.get('layer_score')}/100")
        print(f"{'='*60}\n")

        for name, data in scores.get("platforms", {}).items():
            s = data.get("score", "?")
            mark = "✓" if s >= 7 else "⚠" if s >= 4 else "✗"
            print(f"  {mark} {name:<15} {s}/10")
            print(f"     Evidence:       {data.get('evidence', '')[:150]}")
            print(f"     ICP alignment:  {data.get('content_alignment', '')}")
            print(f"     Now improves:   {data.get('currently_improves', '')}")
            print(f"     If fixed:       {data.get('missed_opportunity', '')}")
            print(f"     → {data.get('recommendation', '')}")
            print()

        print(f"  Top 3 Gaps:")
        for g in scores.get("top_3_gaps", []):
            print(f"    • {g}")
        print(f"\n  {scores.get('summary', '')}")
    except Exception as e:
        print(f"  Scoring failed: {e}")
        import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()
