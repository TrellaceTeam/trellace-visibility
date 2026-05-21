"""
A/B/C classifier: maps every audit finding to its category + specific fix guidance.
Used by unified_runner to enrich output before rendering.
"""

# ── Finding → A/B/C + Fix ──────────────────────────────────────────
# Each entry: (layer, category, "what to do to fix this")
FINDING_FIXES = {
    # L1 — Technical
    "broken_link": ("L1", "A",
        "Remove the broken link or set up a 301 redirect to the correct page. Use Screaming Frog or auditstack crawl to find all broken links in one pass."),
    "missing_title": ("L1", "A",
        "Add a unique, descriptive title tag (50-60 chars) with the primary keyword near the front. Every page needs one."),
    "missing_meta_description": ("L1", "A",
        "Add a unique meta description (150-160 chars) that describes the page content and includes a call to action."),
    "schema_validation": ("L1", "A",
        "Fix JSON-LD schema errors. Validate with Google Rich Results Test. Focus on Organization, Article, FAQ, and SoftwareApplication types."),
    "lcp_slow": ("L1", "B",
        "Optimize the largest visible element: serve images as WebP/AVIF, use a CDN with edge caching, preload the hero image with fetchpriority='high', inline critical CSS, and remove render-blocking resources."),
    "cls_high": ("L1", "B",
        "Set explicit width/height on all images and videos. Use CSS aspect-ratio for responsive containers. Reserve space for ads and embeds. Never inject content above existing content after page load."),
    "no_gsc": ("L1", "A",
        "Connect Google Search Console via OAuth. Verify domain ownership. Data backfill takes 28 days. Free."),
    "missing_schema": ("L1", "A",
        "Add Organization schema site-wide, Article schema on blog posts, FAQ schema on Q&A pages, SoftwareApplication on product pages, BreadcrumbList on all pages. Use JSON-LD format."),

    # L2 — Content
    "content_quality": ("L2", "B",
        "Restructure content into self-contained 134-167 word chunks. Each chunk must open with a declarative answer in the first 40-60 words. Add at least 2-3 specific statistics, dates, or named entities per chunk."),
    "readability_low": ("L2", "B",
        "Shorten sentences to 15-20 words average. Replace complex terms with simpler alternatives. Use Hemingway Editor to check readability. Target Flesch score of 60-70."),
    "missing_author": ("L2", "A",
        "Add author byline with credentials to every content page. Include a short bio with relevant expertise. Link to LinkedIn profile."),
    "no_sources_cited": ("L2", "A",
        "Cite at least 2 sources per major claim. At least 1 must be a primary source. Name the source, not just 'studies show.' Link to the original."),
    "no_original_data": ("L2", "B",
        "Publish original research, surveys, benchmarks, or data analysis. AI weights unique data 2-3× higher than recycled content. Even a simple customer survey counts."),
    "cta_overload": ("L2", "A",
        "Reduce CTAs to 1-2 per page maximum. Too many CTAs signal promotional content to AI systems, which deprioritize promotional content for citations."),

    # L3 — External
    "no_wikipedia": ("L3", "C",
        "Cannot create directly. Build notability through: industry awards, major press coverage (TechCrunch, Forbes, WSJ), significant funding rounds, customer wins from recognizable brands, independent research citations. Wikipedia editors create pages when notability is established."),
    "missing_linkedin": ("L3", "A",
        "Create LinkedIn company page. Fill all fields: logo, description with ICP keywords, website link, industry, company size. Have CEO and team members complete their profiles showing Muir AI affiliation."),
    "missing_g2": ("L3", "A",
        "Create G2 profile in the correct category (Cost Estimation or Supply Chain Analytics, not Sustainability). Add screenshots, demo video, pricing info. Target 10+ reviews from existing customers to get on the Grid."),
    "missing_capterra": ("L3", "A",
        "Create Capterra profile. Use same category alignment as G2. Solicit reviews from customers. 50+ reviews is competitive."),
    "missing_youtube": ("L3", "A",
        "Create YouTube channel. Publish 10+ videos with human-reviewed transcripts, question-format titles, and 3-5 paragraph descriptions. Topics: product demos, industry analysis, how-to guides."),
    "missing_reddit": ("L3", "A",
        "Identify 3-5 relevant subreddits (r/supplychain, r/manufacturing, r/procurement). Participate genuinely — answer questions, share knowledge, be helpful. Never post promotional content. AI detects this."),
    "low_sov": ("L4", "B",
        "Improve Layers 1-3 to increase AI citation readiness. Content citability is the #1 lever. External presence builds corroboration threshold. Changes take 6-8 weeks to show in AI visibility."),
    "sharp_layer_drop": ("L4", "B",
        "Compare current and previous audit. Identify which specific checks degraded. Revert recent site changes that caused the drop. Re-run audit to confirm fix."),

    # L3 platform quality (low scores)
    "low_linkedin_quality": ("L3", "B",
        "Post 2-3×/week from company page and team profiles. Use carousel/PDF formats (7% engagement vs 3-4% for text). Focus on ICP-relevant topics: cost modeling, tariff analysis, supply chain resilience. Personal profiles get 561% more reach."),
    "low_g2_quality": ("L3", "B",
        "Target 60-80+ reviews at 4.5+ stars. Ask every happy customer to leave a review. Respond to all reviews within 48 hours. Keep profile fresh with updated screenshots and pricing."),
    "low_youtube_quality": ("L3", "B",
        "Upload 1-2 videos/month. Use human-reviewed transcripts (not auto-captions). Question-format titles perform best. YouTube mentions have 0.737 correlation with AI visibility."),
    "low_podcast_quality": ("L3", "B",
        "Book 2-4 podcast appearances/month on supply chain, manufacturing, and climate tech shows. Ensure transcripts are published on the show's site or your own. AI visibility from transcripts kicks in 60-90 days after recording."),
    "low_publication_quality": ("L3", "B",
        "Pitch and publish 2-4 contributed articles/year on DR 40+ sites (Supply Chain Dive, IndustryWeek, Manufacturing.net). 96% of AI citations come from third-party sources."),
}


def classify_and_fix(finding: dict) -> dict:
    """Add A/B/C classification, fix guidance, and layer label to a finding."""
    rule_id = finding.get("rule_id", "unknown")
    info = FINDING_FIXES.get(rule_id, ("?","B","Review and improve this area based on the visibility framework benchmarks."))
    layer, category, fix = info
    finding["layer"] = layer
    finding["category"] = category
    finding["fix"] = fix
    return finding


def build_abc_summary(all_findings: list) -> dict:
    """Build per-layer A/B/C summary from classified findings."""
    summary = {"L1": {"A": [], "B": [], "C": []},
               "L2": {"A": [], "B": [], "C": []},
               "L3": {"A": [], "B": [], "C": []},
               "L4": {"A": [], "B": [], "C": []}}

    for f in all_findings:
        layer = f.get("layer", "?")
        cat = f.get("category", "B")
        if layer not in summary:
            layer = "L1"  # default to L1 if unknown
        summary[layer][cat].append(f)

    counts = {}
    for layer in summary:
        counts[layer] = {
            "A": len(summary[layer]["A"]),
            "B": len(summary[layer]["B"]),
            "C": len(summary[layer]["C"]),
            "total": sum(len(v) for v in summary[layer].values()),
        }
    return {"by_layer": summary, "counts": counts}
