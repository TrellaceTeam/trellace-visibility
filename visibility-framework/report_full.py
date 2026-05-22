"""Final HTML — stacked A/B/C, color-coded scores, fix dropdowns."""
import json, os

def _build_actions(layer: str, findings: list) -> list:
    """Build priority actions from classified findings for a given layer."""
    layer_findings = [f for f in findings if f.get("layer") == layer]
    # Deduplicate by rule_id
    seen = {}
    for f in layer_findings:
        rid = f.get("rule_id","unknown")
        if rid not in seen or f.get("priority",0) > seen[rid].get("priority",0):
            seen[rid] = f
    actions = []
    for rid, f in sorted(seen.items(), key=lambda x: x[1].get("priority",0), reverse=True):
        actions.append((rid, f.get("title","")[:100], f.get("effort",3), f.get("what_it_improves","")[:80]))
    return actions

FIXES = {
    "broken_link": (
        "Each broken link wastes Google's crawl budget and sends users to a dead page. "
        "For each broken URL listed: (1) If the page was moved, set up a 301 redirect from the old URL to its new location. "
        "Most website platforms (Webflow, WordPress, Next.js) have a redirects settings page. Add each redirect there. "
        "(2) If the page was deleted and has no replacement, remove all internal links pointing to it so users and crawlers stop finding it. "
        "(3) After fixing, Google Search Console will confirm the errors are resolved within a few days. "
        "If you're using Webflow, go to Settings → Publishing → 301 Redirects. If using a custom setup, add the redirects to your hosting config or .htaccess file."
    ),
    "schema_validation": (
        "Schema markup is machine-readable code that tells Google and AI what each piece of content means. Without it, your content is just text — with it, it becomes structured data that can appear in rich snippets, Knowledge Panels, and AI citations. "
        "Add these JSON-LD schema types: (1) Organization — on every page, describing your company name, logo, and website. (2) Article — on every blog post, with author name, publish date, and headline. (3) FAQPage — on any page with Q&A content, with each question-answer pair. (4) SoftwareApplication — on your product/solution pages, describing what your platform does. (5) BreadcrumbList — on every page, showing the page's position in your site hierarchy. "
        "Implementation: If using Webflow, add custom code in Page Settings → Inside <head> tag. If using a CMS, most SEO plugins (Yoast, RankMath) can add these automatically. After adding, validate every page using Google's Rich Results Test (search 'Google Rich Results Test' — it's a free web tool). Fix any errors it reports. "
        "Expected impact: rich snippets increase click-through rate by 20-30%. AI systems can parse your content structure and are more likely to cite you."
    ),
    "lcp_slow": (
        "LCP (Largest Contentful Paint) measures how long the biggest visible element on your page takes to load. At 17 seconds, visitors are waiting far too long — Google penalizes pages above 2.5 seconds. "
        "Fix in order of impact: (1) Compress and convert all images to WebP or AVIF format — these are 30-50% smaller than JPEG/PNG. Use a tool like Squoosh (squoosh.app, free) or Cloudinary. (2) Set explicit width and height on your hero image so the browser reserves space before loading. (3) Add fetchpriority='high' to your main hero image tag. (4) If using a CMS like Webflow, enable the built-in image optimization and lazy loading settings. (5) Use a CDN (Content Delivery Network) — Cloudflare offers a free plan that caches your content at edge locations worldwide. (6) Remove or defer any JavaScript that blocks rendering — move analytics tags, chat widgets, and third-party scripts to load after the page content. "
        "Verify with Google PageSpeed Insights (free) — run it before and after to measure improvement."
    ),
    "cls_high": (
        "CLS (Cumulative Layout Shift) measures visual stability — how much things jump around while the page loads. Scores above 0.1 are penalized by Google. "
        "Fix: (1) Set explicit width and height attributes on every image and video element. Without these, the browser doesn't know how much space to reserve and content shifts when images load. (2) For responsive containers, use CSS aspect-ratio. (3) Never inject content above existing content after the page loads — this includes cookie banners, promo popups, and dynamic ads. If you must show a banner, reserve space for it. (4) Use font-display: optional or swap for web fonts so text doesn't jump when fonts load. "
        "Verify with Google PageSpeed Insights or Chrome DevTools (Lighthouse tab)."
    ),
    "content_quality": (
        "AI systems don't rank whole pages — they break content into chunks of ~150 words and decide which chunks are worth citing. If your chunks aren't self-contained and fact-dense, AI skips them. "
        "For each important page: (1) Break content into paragraphs of 134-167 words each. (2) Every paragraph must make complete sense read in isolation — no 'as mentioned above' or 'click here for more.' (3) Open each section with a direct answer in the first 40-60 words — don't bury the conclusion. (4) Add 2-3 specific data points per paragraph: statistics, percentages, dollar amounts, named companies, dates. For example: 'Our platform processes 10,000+ supplier quotes daily, identifying cost reduction opportunities averaging 12-15% per product line.' Not: 'Our platform helps reduce costs.' (5) Cite sources for major claims. Instead of 'studies show,' say 'According to McKinsey's 2025 Manufacturing Report.' "
        "Expected impact: content optimized this way is 2-3x more likely to be retrieved and cited by AI systems like ChatGPT and Perplexity."
    ),
    "readability_low": (
        "Flesch Reading Ease measures how complex your writing is. Score of 16 means very difficult — Harvard Law Review level. B2B content should target 60-70, which is accessible to a professional audience without being dense. "
        "Fix: (1) Shorten sentences to 15-20 words on average. Break long sentences into two. (2) Replace jargon with simpler alternatives where possible — say 'use' instead of 'utilize,' 'cost' instead of 'cost expenditure.' (3) Use active voice: 'The platform analyzes data' not 'Data is analyzed by the platform.' (4) Add section breaks, bulleted lists, and clear headings to make content scannable. (5) Use Hemingway Editor (hemingwayapp.com, free) to check readability. Paste your content, it highlights complex sentences. Rewrite anything marked red. "
        "This isn't about dumbing down — it's about making your expertise accessible. Even technical buyers prefer clear writing."
    ),
    "missing_g2": (
        "G2 is the #1 software review platform for B2B. Critically: 100% of tools cited by ChatGPT have G2 profiles. Without one, you're invisible to AI recommendation engines. "
        "Steps: (1) Go to g2.com, search for your company, claim or create your profile. (2) Fill every field: company description with key terms your buyers search for (should-cost modeling, product cost estimation, tariff analysis), high-quality screenshots of your platform, a 2-3 minute demo video, and pricing information. (3) List under the correct categories — 'Cost Estimation' or 'Supply Chain Analytics,' not 'Sustainability' (wrong category misleads both buyers and AI). (4) Send review requests to current customers — target 10 reviews minimum to appear on G2's Grid. Provide a direct link. Most customers are happy to leave reviews when asked. (5) Respond to every review within 48 hours — G2 rewards active profiles. "
        "Expected impact: G2 profile is the single most important external presence action for AI visibility."
    ),
    "missing_capterra": (
        "Capterra is the second major software review platform. 99% of tools cited by ChatGPT have Capterra profiles. "
        "Steps: (1) Go to capterra.com, claim or create your profile. (2) Same setup as G2 — complete every field, add screenshots and demo. (3) Use the same category alignment as G2. (4) Target 50+ reviews to be competitive in your category. "
        "Note: even if you don't drive much direct traffic from Capterra, the profile is an AI inclusion gate — it signals to AI systems that you're a real, reviewed company in your category."
    ),
    "missing_youtube": (
        "YouTube mentions are the single strongest predictor of AI visibility — 0.737 correlation (Ahrefs study of 75,000 brands). AI doesn't watch videos — it reads transcripts. "
        "Steps: (1) Create a YouTube channel for your company. (2) Publish 10+ videos covering: product demos (5-8 minutes), industry analysis (e.g., 'How tariff changes affect manufacturing costs in 2026'), how-to guides (e.g., 'How to build a should-cost model for a consumer electronics product'). (3) For every video: write a 3-5 paragraph description that includes the key points and relevant keywords. Use question-format titles ('How to Reduce Product Manufacturing Costs?'). Upload human-reviewed captions — automatic captions often mangle brand names and technical terms. YouTube Studio lets you edit auto-captions or upload a transcript file. (4) Add chapters/timestamps so AI can cite specific segments. "
        "Expected impact: transcripts get indexed by Google and Bing, feeding both traditional search and AI retrieval. 29.5% of Google AI Overviews cite YouTube content."
    ),
    "no_wikipedia": (
        "A Wikipedia page provides a massive boost to AI entity recognition — AI systems use Wikipedia as a trusted source for verifying company existence and details. However, companies cannot create their own Wikipedia page — it will be deleted. Wikipedia requires independent, reliable sources to establish notability. "
        "What you can do: (1) Get covered by major press — TechCrunch, Forbes, WSJ, industry publications. (2) Win industry awards. (3) Announce significant funding rounds or customer wins. (4) Publish original research that gets cited by others. When enough independent sources exist, a Wikipedia editor will create the page. "
        "Near-term alternative: ensure your Wikidata entry and Crunchbase profile are accurate and complete. These also feed AI entity recognition systems."
    ),
    "canonical_url": (
        "Canonical URLs tell Google which version of a page is the 'official' one when the same content exists at multiple URLs. Without them, Google may index duplicates and split your ranking power across multiple URLs. "
        "Fix: add a <link rel='canonical' href='https://www.muir.ai/page-url'> tag in the <head> of every page, pointing to the preferred version. In Webflow, go to Page Settings → SEO → Canonical URL. If pages don't have duplicates, set the canonical to the page's own URL. "
        "Verify by viewing the page source and searching for 'canonical'."
    ),
    "breadcrumb": (
        "Breadcrumb navigation shows users and search engines where a page sits in your site hierarchy (e.g., Home > Solutions > Should-Cost Modeling). It enables breadcrumb rich results in Google and helps AI understand your site structure. "
        "Fix: add BreadcrumbList schema markup to every page. Also add visible breadcrumb links at the top of each page. In Webflow, use the built-in breadcrumb element or add custom code. "
        "Verify with Google Rich Results Test — it should detect the BreadcrumbList schema."
    ),
    "heading_hierarchy": (
        "Proper heading structure (one H1 per page, H2s for main sections, H3s for subsections) helps both Google and AI understand your content. Pages with clean hierarchies have 2.8x higher AI citation odds. "
        "Fix: (1) Ensure every page has exactly one H1 tag containing the primary topic. (2) Use H2 tags for each major section. (3) Use H3 tags for subsections under H2s. (4) Don't skip levels — go H1→H2→H3, not H1→H3. "
        "In Webflow, use the Heading element with the correct level. Verify by viewing page source or using a browser extension like 'HeadingsMap.'"
    ),
    "single_h1": (
        "Multiple H1 tags on a single page confuse search engines about which topic is most important. Every page should have exactly one H1. "
        "Fix: Find pages with multiple H1 tags (our audit detected them). Change all but the primary H1 to H2 or H3 tags. The H1 should contain the page's main topic."
    ),
    "caching": (
        "Cache-Control headers tell browsers and CDNs how long to store copies of your images, CSS, and JavaScript files. Without caching, every visitor re-downloads everything on every visit, slowing down your site and wasting bandwidth. "
        "Fix: add Cache-Control headers to your server or CDN configuration. Set long cache times for static assets (images, fonts, CSS: 1 year) and short times for HTML pages (1 hour). If using Cloudflare (free plan available), enable 'Auto Minify' and set Browser Cache TTL to 1 year. "
        "Verify by checking response headers in Chrome DevTools (Network tab → click any image → Headers → Cache-Control)."
    ),
    "alt_text": (
        "Alt text describes images for screen readers and search engines. Missing alt text reduces accessibility and eliminates opportunities to appear in Google Image Search. "
        "Fix: add descriptive alt text to every image. For product screenshots: 'Muir AI should-cost modeling dashboard showing cost breakdown by component.' For logos: 'Muir AI logo.' For decorative images, use alt=''. In Webflow, add alt text in the Image Settings panel."
    ),
    "author_bios": (
        "Author bios show who wrote the content and why they're qualified. This is a key E-E-A-T signal for both Google and AI — content without visible authorship is less trusted. "
        "Fix: add an author byline to every blog post and article. Include the author's name, role, and a one-sentence credential. Example: 'By Harris Chalat, CEO at Muir AI. Former SpaceX engineer focused on supply chain intelligence.' Link to a full bio page or LinkedIn profile. "
        "In Webflow, add an author field to your blog post template."
    ),
    "author_credentials": (
        "Stating author qualifications (experience, background, expertise) strengthens the Expertise signal in Google's E-E-A-T framework. AI systems use this to determine content trustworthiness. "
        "Fix: in each author bio, include specific credentials relevant to the topic. Examples: '15 years in manufacturing procurement,' 'Led should-cost analysis for 200+ product lines,' 'Published in Supply Chain Management Review.' Generic bios like 'content team' don't count."
    ),
    "external_sources": (
        "Citing external sources demonstrates that your content is researched and fact-based, not just marketing opinion. AI systems check for source citations when deciding which content to trust and cite. "
        "Fix: for every major claim or statistic, link to the original source. Use named sources: 'According to the US International Trade Commission's 2025 report...' not 'Studies show...' Target 2-3 external citations per major content page. Link to credible, high-authority sources (government data, industry reports, academic research)."
    ),
    "last_updated": (
        "Visible dates tell both users and AI how current your content is. AI heavily weights freshness — 70% of AI-cited pages have been updated in the past year. Pages without dates are assumed to be old. "
        "Fix: add a 'Last updated: [Month Year]' line to every content page. Set it as part of your page template so it appears automatically. For blog posts, the publish date is sufficient. For solution pages, add a last-reviewed date and update it at least every 6 months."
    ),
    "original_data": (
        "Original data — company surveys, benchmarks, analysis, case study metrics — is weighted 2-3x higher by AI than recycled content. It's unique to you and can't be found elsewhere, making it highly citable. "
        "Fix: publish at least one original data asset per quarter. Examples: survey of 100 procurement leaders on cost estimation challenges, analysis of tariff impact across 500 product categories using your platform data, benchmark report on should-cost modeling adoption by industry. Even a simple internal analysis turned into a public report counts."
    ),
    "lists": (
        "Bulleted and numbered lists make content scannable and extractable. 80% of AI-cited pages use lists to present key information in digestible format. "
        "Fix: convert long paragraphs of features, benefits, or steps into bulleted lists. For step-by-step instructions, use numbered lists. For key takeaways, use bullets. Each list item should be one clear point. Don't overdo it — use lists where they add clarity, not as a replacement for substance."
    ),
    "case_studies": (
        "Case studies are the strongest form of social proof for B2B buyers. They show real results with specific numbers, giving prospects confidence and giving AI systems concrete data to cite. "
        "Fix: publish 3-5 case studies on your site. For each: name the customer (with permission), describe the problem they had, show specific metrics (e.g., 'reduced cost estimation time from 2 weeks to 4 hours'), and include a quote. Even anonymized case studies with real numbers are valuable."
    ),
    "missing_reddit": (
        "Reddit is a major source for AI systems — 46.7% of Perplexity citations come from Reddit. AI treats Reddit discussions as authentic user sentiment, making it powerful for building the corroboration threshold. "
        "How to do it right: (1) Identify 3-5 relevant subreddits — r/supplychain, r/manufacturing, r/procurement are good starting points. (2) Create a personal account (not a company account — users and AI detect promotional accounts). (3) Participate genuinely for 2-3 weeks before mentioning Muir — answer questions, share knowledge, be helpful. (4) When you do mention Muir, only do so when it's the actual best answer to someone's question. (5) Never post 'check out Muir AI' — AI systems detect and deprioritize promotional content. One genuine, helpful comment that happens to mention Muir is worth 100 promotional posts."
    ),
    "low_linkedin_quality": (
        "LinkedIn is where B2B buyers spend their professional attention. Your company page has good follower count but needs active posting to drive awareness, branded search, and AI visibility. "
        "Steps: (1) Post from the company page 2-3 times per week. (2) Have the CEO and key team members post from their personal profiles 1-2 times per week — personal profiles get 561% more reach than company pages. (3) Best-performing formats: PDF carousels (7% engagement rate), multi-image posts (6.6%), polls (6-12%). Avoid posts with external links — LinkedIn penalizes them. (4) Content topics: case studies, industry analysis, product insights, customer results. Posts that share specific data or lessons perform best. (5) Engage with comments within the first 60-90 minutes — this determines 75% of total reach. "
        "What this improves: branded search volume (people Google you after seeing posts), outbound acceptance rate (prospects recognize your name), and retargeting pool size."
    ),
}

def render_full_html(ctx: dict, output_path: str):
    l1,l2,l3,l4 = ctx.get("l1",{}),ctx.get("l2",{}),ctx.get("l3",{}),ctx.get("l4",{})
    enrich = ctx.get("enrichment",{})
    all_f = ctx.get("all_findings", [])
    es = enrich.get("summary",{})
    eeat = enrich.get("eeat",{})
    faq_q = enrich.get("faq_quality",{})
    llms = enrich.get("llms_txt",{})
    rems = ctx.get("remediations",[])

    def sc(s):
        if s is None: return ("#94a3b8","?",0)
        if s>=80: return ("#16a34a","A",100)
        if s>=60: return ("#2563eb","B",75)
        if s>=40: return ("#ca8a04","C",50)
        if s>=20: return ("#ea580c","D",25)
        return ("#dc2626","F",10)

    def gate(name, ok, detail="", expand="", desc=""):
        c,bg = ("#16a34a","#f0fdf4") if ok else ("#dc2626","#fef2f2")
        ic = "✓" if ok else "✗"
        exp = ""
        if expand:
            eid = abs(hash(name))%100000
            exp = f'<span style="cursor:pointer;margin-left:6px;font-size:.75rem;color:#2563eb" onclick="document.getElementById(\'e{eid}\').classList.toggle(\'hidden\')">[+]</span><div id="e{eid}" class="hidden" style="margin-top:4px;padding:8px 12px;background:#f8fafc;border-radius:6px;font-size:.8rem;color:#475569;border-left:3px solid #e2e8f0">{expand}</div>'
        desc_html = f'<div style="font-size:.7rem;color:#94a3b8;margin-top:1px">{desc}</div>' if desc else ""
        return f'<tr><td style="font-size:.9rem;padding:8px 10px">{name}{desc_html}</td><td style="text-align:center;padding:8px 10px"><span style="display:inline-block;width:28px;height:28px;line-height:28px;border-radius:7px;background:{bg};color:{c};font-weight:700;font-size:.85rem">{ic}</span></td><td style="font-size:.8rem;color:#64748b;padding:8px 10px">{detail}{exp}</td></tr>'

    def bar(name, val, target, unit="", invert=False, scale=None, desc=""):
        if val is None: return f'<tr><td style="font-size:.9rem;padding:8px 10px">{name}</td><td colspan="2" style="font-size:.8rem;color:#94a3b8;padding:8px 10px">not measured</td></tr>'
        if val == 0 and target > 0:
            return f'<tr><td style="font-size:.9rem;padding:8px 10px">{name}</td><td style="font-size:.9rem;font-weight:600;padding:8px 10px;color:#dc2626">0{unit}</td><td style="font-size:.8rem;color:#64748b;padding:8px 10px"><span style="color:#dc2626;font-weight:600">Poor</span> · target {target}{unit}<div style="margin-top:4px;height:5px;background:#e2e8f0;border-radius:3px;width:100%"><div style="height:5px;background:#dc2626;border-radius:3px;width:2px"></div></div></td></tr>'
        if scale is None: scale = target * 1.5 if target > 0 else 10  # default scale
        # How close to target (0=far, 1=at target, >1=exceeds)
        closeness = min(1, max(0, target/max(1,val) if invert else val/max(1,target)))
        bar_pct = min(100, int((val / max(1, scale)) * 100))  # bar relative to scale, not target
        bc = "#16a34a" if closeness > 0.8 else "#ca8a04" if closeness > 0.4 else "#dc2626"
        status = "Good" if closeness > 0.8 else "Needs work" if closeness > 0.4 else "Poor"
        desc_html = f'<div style="font-size:.7rem;color:#94a3b8;margin-top:2px">{desc}</div>' if desc else ""
        return f'<tr><td style="font-size:.9rem;padding:8px 10px">{name}{desc_html}</td><td style="font-size:.9rem;font-weight:600;padding:8px 10px">{val}{unit}</td><td style="font-size:.8rem;color:#64748b;padding:8px 10px"><span style="color:{bc};font-weight:600">{status}</span> · target {target}{unit}<div style="margin-top:4px;height:5px;background:#e2e8f0;border-radius:3px;width:100%"><div style="height:5px;background:{bc};border-radius:3px;width:{bar_pct}%"></div></div></td></tr>'

    def act_fix(rule_id: str) -> str:
        return FIXES.get(rule_id, "Review this area and apply visibility framework best practices.")

    # ── L1 ──
    broken = l1.get("broken_links",0)
    schema_c = l1.get("schema_types",0)
    lcp = l1.get("lcp_ms"); cls = l1.get("cls")
    perf = l1.get("performance"); seo = l1.get("seo_score")
    pages_with_schema = es.get("pages_with_schema",0); pages_total = max(1,es.get("total_pages",1))
    schema_detail = f"Schema on {pages_with_schema}/{pages_total} pages: " + ", ".join(f"{t}:{c}" for t,c in es.get("schema_type_counts",{}).items()) if es.get("schema_type_counts") else f"0 of {pages_total} pages have schema"
    broken_detail = "<br>".join(l1.get("broken_urls",[])[:5]) if broken else ""

    l1a = [
        gate("HTTPS valid", True, "Secure connection — Google ranking baseline", "", "Encrypts data between browser and server. Required for trust and ranking."),
        gate("Sitemap present", l1.get("pages_crawled",0)>0, f"{l1.get('pages_crawled',0)} pages indexed", "", "XML file listing all pages for search engines to discover and index."),
        gate("No broken links", broken==0, f"{broken} broken links found" if broken else "All links valid", broken_detail, "Dead URLs that return 404 errors. Waste crawl budget and frustrate users."),
        gate("Mobile responsive", l1.get("accessibility",0) and l1.get("accessibility",0)>0.9, f"Accessibility {l1.get('accessibility',0):.0%}" if l1.get("accessibility") else "Not checked", "", "Site adapts layout for phone screens. Google uses mobile-first indexing."),
        gate("AI crawlers allowed", l1.get("robots_disallows","")==0, "GPTBot, ClaudeBot, PerplexityBot all allowed in robots.txt", "", "Tells AI crawlers they can access your content. Blocking them = invisible to ChatGPT, Claude, Perplexity."),
        gate("llms.txt exists", llms.get("exists",False), f"{llms.get('size_bytes',0)} bytes, {llms.get('lines',0)} links" if llms.get("exists") else "Not found — create at muir.ai/llms.txt", "", "AI-native sitemap. Guides LLMs to your most important pages. Emerging standard."),
        gate("Schema markup", pages_with_schema>0, f"{pages_with_schema}/{pages_total} pages have schema" if pages_with_schema>0 else "No schema on any page — AI cannot parse content", schema_detail if len(schema_detail)>10 else "", "Machine-readable labels (JSON-LD) telling Google and AI what each page is about: an article, a product, a FAQ."),
        gate("Canonical URLs", es.get("has_canonical_pct",0)>0.8, f"{es.get('has_canonical_pct',0):.0%} of pages have canonical tags", "", "Tells Google which version of a page is the 'main' one, preventing duplicate content penalties."),
        gate("Breadcrumb navigation", es.get("has_breadcrumb_pct",0)>0.5, f"{es.get('has_breadcrumb_pct',0):.0%} of pages", "", "Trail of links showing page position in site hierarchy (Home > Solutions > Should-Cost). Helps Google understand structure."),
        gate("Heading hierarchy (H1→H2→H3)", es.get("has_headings_pct",0)>0.8, f"{es.get('has_headings_pct',0):.0%} of pages. Single H1: {es.get('single_h1_pct',0):.0%}. Avg {es.get('avg_h1',0):.1f} H1s/page", "", "Proper heading structure: one H1 per page, H2s for sections, H3s for subsections. 2.8x higher AI citation odds with clean hierarchy."),
    ]
    l1b = [
        bar("LCP — Largest Contentful Paint", round(lcp) if lcp else None, 2500, "ms", True, 10000, "How long until the main content loads"),
        bar("CLS — Cumulative Layout Shift", round(cls,3) if cls else None, 0.1, "", True, 0.5, "How much content shifts during loading"),
        bar("TTFB — Time to First Byte", es.get("avg_ttfb_ms"), 200, "ms", True, 1000, "Server response time"),
        bar("Lighthouse Performance", round(perf*100) if perf else None, 90, "", False, 100, "Overall page quality score (0-100)"),
        bar("Lighthouse SEO", round(seo*100) if seo else None, 90, "", False, 100, "SEO fundamentals score"),
        bar("Caching headers", ((es.get("has_caching_pct") or 0) * 100), 100, "%", False, 100, "% of pages with Cache-Control set"),
        bar("Image alt text", es.get("alt_text_pct",0)*100 if es.get("alt_text_pct") else None, 100, "%", False, 100, "% of images with descriptive alt text"),
    ]

    l1_actions = _build_actions("L1", all_f)

    # ── L2 ──
    cit = l2.get("avg_citability",0); fl = l2.get("avg_flesch",0)
    pages = l2.get("pages",[])
    l2_faq_detail = f"FAQ found on {es.get('pages_with_faq',0)}/{es.get('total_pages',0)} pages"
    for normed, q in faq_q.items():
        l2_faq_detail += f"<br>{normed[:50]}: {q.get('score',0)}/10 — {q.get('evidence','')[:80]}"

    l2a = [
        gate("Author bios", es.get("has_author_pct",0)>0, f"{es.get('has_author_pct',0):.0%} of pages show who wrote the content", "", "Visible author name on each article. AI and Google use author signals for E-E-A-T credibility scoring."),
        gate("Author credentials", es.get("has_credentials_pct",0)>0, f"{es.get('has_credentials_pct',0):.0%} of pages state qualifications", "", "Author's expertise stated (role, background, experience). Strong E-E-A-T signal for AI trust."),
        gate("External sources cited", es.get("has_external_sources_pct",0)>0, f"{es.get('has_external_sources_pct',0):.0%} of pages reference external sources", "", "Links and references to credible third-party sources. Shows research backing claims."),
        gate("Last-updated dates visible", es.get("has_last_updated_pct",0)>0, f"{es.get('has_last_updated_pct',0):.0%} of pages show dates", "", "Visible publish/update dates on content. AI weights recent content higher. 70% of AI-cited pages updated within past year."),
        gate("Original data presented", es.get("has_original_data_pct",0)>0, f"{es.get('has_original_data_pct',0):.0%} of pages have original data", "", "Company-generated surveys, benchmarks, or analysis. AI weights unique data 2-3x higher than recycled content."),
        gate("Bulleted/numbered lists", es.get("has_lists_pct",0)>0, f"{es.get('has_lists_pct',0):.0%} of pages use lists", "", "Bulleted or numbered lists make content scannable. 80% of AI-cited pages use lists for key information."),
        gate("FAQ sections", es.get("pages_with_faq",0)>0, l2_faq_detail, l2_faq_detail, "Question-and-answer sections matching what buyers ask. FAQ content gets extracted by AI for featured snippets and citations."),
        gate("Case studies", es.get("has_case_study_pct",0)>0, f"{es.get('has_case_study_pct',0):.0%} of pages", "", "Real customer success stories with specific results. Social proof for buyers. AI authority signal."),
    ]
    l2b = [
        bar("Chunk citability (avg)", round(cit,1) if cit else None, 7, "/10", False, 10, "How likely AI is to retrieve and cite each chunk"),
        bar("Flesch readability (avg)", round(fl) if fl else None, 60, "", False, 100, "Reading ease — 60-70 is ideal for B2B"),
        bar("E-E-A-T quality", round(sum(e.get("eeat_score",0) for e in eeat.values())/max(1,len(eeat))) if eeat else None, 80, "", False, 100, "Experience, Expertise, Authority, Trustworthiness"),
        bar("FAQ quality", round(sum(q.get("score",0) for q in faq_q.values())/max(1,len(faq_q)),1) if faq_q else None, 7, "/10", False, 10, "Relevance and clarity of FAQ content"),
    ]

    l2_actions = _build_actions("L2", all_f)

    # ── L3 ──
    plats = l3.get("platforms",{})
    l3a, l3b = [], []
    for pname in ["LinkedIn","G2","Capterra","YouTube","Reddit","Wikipedia"]:
        pdata = plats.get(pname,{})
        exists = pdata.get("score",0) > 0
        l3a.append(gate(f"{pname} presence", exists, f"Score: {pdata.get('score')}/10" if exists else "Not found on this platform"))
    for pname in ["LinkedIn","G2","Capterra","YouTube","Podcasts","Publications"]:
        pdata = plats.get(pname,{})
        s = pdata.get("score",0)
        l3b.append(bar(f"{pname} quality", s, 7, "/10"))

    l3_actions = _build_actions("L3", all_f)


    # ── L4 ──
    sov = l4.get("sov",{})
    l4_rows = ""
    all_models = ["chatgpt-4o","chatgpt-mini","claude-sonnet","claude-haiku","perplexity-sonar","gemini-flash","copilot"]
    for m in all_models:
        s = sov.get(m)
        if s is not None:
            l4_rows += f'<tr><td>{m}</td><td style="font-weight:600;color:#dc2626">{int(s*100)}%</td><td><span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:600">Active</span></td></tr>'
        else:
            l4_rows += f'<tr><td style="color:#94a3b8">{m}</td><td style="color:#94a3b8">—</td><td><span style="background:#f1f5f9;color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:.75rem">API key needed</span></td></tr>'

    page_rows = ""
    for p in pages:
        ps,pg,pct = sc(p.get("page_score"))
        page_rows += f'<tr><td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{p.get("url","")[-50:]}</td><td style="font-weight:600;color:{ps}">{p.get("page_score","?")}</td><td>{p.get("avg_citation_worthiness","")}</td><td>{p.get("flesch","")}</td></tr>'

    plat_rows = ""
    for name, pdata in plats.items():
        ps,_,_ = sc(pdata.get("score","?"))
        missed = pdata.get("missed_opportunity","")[:100]
        rec = pdata.get("recommendation","")[:100]
        plat_rows += f'<tr><td style="font-weight:600">{name}</td><td style="font-weight:600;color:{ps}">{pdata.get("score","?")}/10</td><td style="font-size:.8rem;max-width:180px">{pdata.get("evidence","")[:100]}</td><td style="font-size:.8rem;max-width:160px">{"🔒 "+missed if missed else ""}</td><td style="font-size:.8rem;max-width:180px">{rec}</td></tr>'

    def actions_html(label, acts):
        rows = ""
        for rule_id, action, effort, impact in acts:
            eid = abs(hash(action))%100000
            fix = act_fix(rule_id)
            ico = "🟢" if effort==1 else "🟡" if effort==2 else "🔴" if effort>=4 else "🟠"
            idx = acts.index((rule_id,action,effort,impact)) + 1
            rows += f"""<tr>
<td style="text-align:center;font-weight:700;width:30px">#{idx}</td>
<td style="font-size:.9rem">{action} <span style="cursor:pointer;font-size:.75rem;color:#2563eb;margin-left:4px" onclick="document.getElementById('fix{eid}').classList.toggle('hidden')">[how?]</span>
<div id="fix{eid}" class="hidden" style="margin-top:4px;padding:8px 12px;background:#fffbeb;border-left:3px solid #f59e0b;border-radius:4px;font-size:.8rem;color:#92400e">{fix}</div></td>
<td style="text-align:center">{ico} {effort}/5</td>
<td style="font-size:.8rem;color:#475569">{impact}</td></tr>"""
        return f"""<div style="margin-top:20px"><h4 style="font-size:.85rem;color:#1e293b;margin-bottom:8px">📋 {label}</h4>
<table><tr><th style="width:30px">#</th><th>Action</th><th style="width:60px">Effort</th><th>Impact</th></tr>{rows}</table></div>"""

    def layer_html(num, label, score_data, improve, a_rows, b_rows, m_rows, c_items, acts):
        color,grade,pct = sc(score_data)
        bar_w = pct
        bar_c = color
        return f"""<div class="sec"><h2 onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('cld')"><span class="arr">▶</span> L{num} — {label} <span style="margin-left:auto;font-size:1.5rem;font-weight:700;color:{color}">{score_data}/100</span><span style="font-size:.8rem;color:{color};margin-left:8px">Grade {grade}</span></h2>
<div class="coll cld">
<div style="font-size:.85rem;color:#475569;margin-bottom:16px">→ If this score improved: {improve}</div>
<div style="margin-bottom:20px"><h4 style="font-size:.8rem;color:#64748b;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em">🟢 A — Binary Gates</h4><table>{"".join(a_rows)}</table></div>
<div style="margin-bottom:20px"><h4 style="font-size:.8rem;color:#64748b;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em">🔵 B — Quality Levels (improve directly)</h4><table>{"".join(b_rows)}</table></div>
<div style="margin-bottom:20px"><h4 style="font-size:.8rem;color:#64748b;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em">📊 Metrics (outcomes of fixing A+B)</h4><table>{"".join(m_rows)}</table></div>
<div style="margin-bottom:20px"><h4 style="font-size:.8rem;color:#64748b;margin-bottom:4px;text-transform:uppercase;letter-spacing:.05em">⚪ C — Uncontrollable</h4><div style="font-size:.8rem;color:#475569;padding:8px 12px;background:#f8fafc;border-radius:6px">{c_items}</div></div>
{actions_html("Priority Actions", acts)}
</div></div>"""

    # ── Assemble ──
    l1_html = layer_html(1, "Technical Foundation", l1.get("score",0),
        "Google ranking would rise, ad CPC would drop ~30%, and AI could parse your content structure.",
        l1a, l1b, l1b,
        "Google algorithm updates can change Core Web Vitals weighting. CDN/WAF may silently block AI crawlers regardless of robots.txt settings.",
        l1_actions)

    l2_html = layer_html(2, "Content Citability", l2.get("score",0),
        "AI would cite your content more often, organic search traffic would increase, and visitors reading your content would be more likely to book a demo.",
        l2a, l2b, l2b,
        "AI model content weighting changes over time. Competitors improving their content quality raises the bar for everyone.",
        l2_actions)
    l2_html += f"""<div class="sec" style="margin-top:8px"><h4 style="font-size:.85rem;margin-bottom:8px">Per-page Scores</h4><table><tr><th>Page</th><th>Score</th><th>Citability</th><th>Flesch</th></tr>{page_rows}</table></div>"""

    l3_html = layer_html(3, "External Presence", l3.get("score",0),
        "AI would trust Muir as a real company — the corroboration threshold. Outbound emails would get higher reply rates. Buyers Googling you would find social proof that seals the deal.",
        l3a, l3b, l3b,
        "Wikipedia page creation (must be done by independent editor when notability is established). Organic YouTube/Reddit mentions by third parties. Industry publication coverage.",
        l3_actions)
    l3_html += f"""<div class="sec" style="margin-top:8px"><h4 style="font-size:.85rem;margin-bottom:8px">Platform Detail</h4><table><tr><th>Platform</th><th>Score</th><th>Evidence</th><th>What's at Stake</th><th>How to Fix</th></tr>{plat_rows}</table></div>"""

    l4_html = f"""<div class="sec"><h2 onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('cld')"><span class="arr">▶</span> L4 — AI Visibility <span style="margin-left:auto;font-size:1.5rem;font-weight:700;color:#dc2626">0/100</span><span style="font-size:.8rem;color:#dc2626;margin-left:8px">Grade F</span></h2>
<div class="coll cld">
<div style="font-size:.85rem;color:#475569;margin-bottom:16px">→ L4 is the scoreboard. It shows whether L1-L3 improvements are translating into actual AI visibility. 30 ICP-accurate prompts × 3 repeats × 4 active models = 360 queries per audit.</div>
<table style="margin-bottom:16px"><tr><th>Model</th><th>SOV</th><th>Status</th></tr>{l4_rows}</table>
<div style="font-size:.8rem;color:#94a3b8">SOV = Share of Voice. % of AI responses mentioning Muir for should-cost modeling queries. Industry: 15%+ = emerging brand, 40%+ = category leader. 3 additional models ready when API keys arrive (Perplexity, Gemini, Copilot).</div>
</div></div>"""

    rem_html = ""
    if rems:
        rr = ""
        for r in rems:
            rr += f'<div style="padding:14px 0;border-bottom:1px solid #e2e8f0"><div style="font-weight:600;font-size:.8rem;color:#64748b;margin-bottom:6px">Fixing: {r.get("for","")}</div><div style="font-size:.9rem;padding:12px 16px;background:#f0fdf4;border-left:3px solid #22c55e;border-radius:6px;margin-bottom:6px">{r.get("draft","")}</div></div>'
        rem_html = f'<div class="sec"><h2 onclick="this.classList.toggle(\'open\');this.nextElementSibling.classList.toggle(\'cld\')"><span class="arr">▶</span> ✏️ Content Fixes (LLM-generated)</h2><div class="coll cld">{rr}</div></div>'

    cc,gc,_ = sc(ctx.get("composite",0))

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Trellace Visibility Audit — {ctx.get('url','')}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f8fafc;color:#0f172a;line-height:1.6}}
.ctr{{max-width:900px;margin:0 auto;padding:24px 20px}}
.hdr{{background:linear-gradient(135deg,#0f172a,#1e293b);color:#fff;border-radius:16px;padding:36px 40px;margin-bottom:28px}}
.hdr .url{{font-size:1.4rem;font-weight:700;word-break:break-all;margin-top:4px}}
.hdr .sub{{font-size:.75rem;opacity:.5;text-transform:uppercase;letter-spacing:.1em}}
.hdr .comp{{display:flex;gap:32px;margin-top:20px;align-items:center}}
.hdr .big{{font-size:3.2rem;font-weight:800;line-height:1;color:{cc}}}
.hdr .stats{{font-size:.8rem;opacity:.6}}
.sec{{background:#fff;border-radius:14px;padding:28px 32px;margin-bottom:18px;box-shadow:0 1px 3px rgba(0,0,0,.05);border:1px solid #f1f5f9}}
.sec h2{{font-size:1rem;margin-bottom:0;cursor:pointer;display:flex;align-items:center;gap:8px;font-weight:700}}
.sec h2 .arr{{font-size:.75rem;transition:transform .2s}}
.coll{{max-height:8000px;overflow:hidden;transition:max-height .35s;margin-top:20px}}
.cld{{max-height:0!important;margin-top:0}}
table{{width:100%;border-collapse:collapse;font-size:.85rem}}
th{{text-align:left;padding:8px 10px;border-bottom:2px solid #e2e8f0;color:#64748b;font-weight:600;text-transform:uppercase;font-size:.7rem;letter-spacing:.05em}}
td{{padding:8px 10px;border-bottom:1px solid #f8fafc}}
.hidden{{display:none}}
.foot{{text-align:center;padding:32px;color:#94a3b8;font-size:.75rem}}
@media(max-width:640px){{.hdr{{padding:24px}}.hdr .big{{font-size:2.2rem}}.hdr .comp{{flex-direction:column;align-items:flex-start}}.sec{{padding:20px 18px}}}}
</style></head><body><div class="ctr">
<div class="hdr"><div class="sub">Visibility Audit</div><div class="url">{ctx.get('url','')}</div>
<div class="comp"><div class="big">{ctx.get('composite','?')}</div><div><div class="stats">Composite — Grade {gc}</div></div></div></div>
{l1_html}{l2_html}{l3_html}{l4_html}{rem_html}
<div class="foot">Trellace Visibility Framework v2 · {ctx.get('audit_id','')} · {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
</div><script>document.querySelectorAll('.sec h2').forEach(h=>{{h.classList.add('open');h.nextElementSibling.classList.remove('cld')}})</script></body></html>"""

    with open(output_path,"w") as f: f.write(html)
    return output_path
