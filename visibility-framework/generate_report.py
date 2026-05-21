"""Standalone report generator — runs enrichment, builds context, generates HTML.
Usage: python generate_report.py [audit_dir] [--url https://...]
"""
import json, os, sys, httpx, xml.etree.ElementTree as ET

def main():
    # Find latest audit
    audit_dirs = sorted([d for d in os.listdir("audits") if os.path.isdir(f"audits/{d}") and os.path.exists(f"audits/{d}/v1/stages")])
    if not audit_dirs:
        print("No audits found")
        return 1
    target = sys.argv[1] if len(sys.argv) > 1 else f"audits/{audit_dirs[-1]}"
    url = sys.argv[2] if len(sys.argv) > 2 else "https://www.muir.ai"
    latest = target if target.startswith("audits/") else f"audits/{audit_dirs[-1]}"

    # Load stages
    stages_dir = f"{latest}/v1/stages"
    stages = {}
    for fname in os.listdir(stages_dir):
        if fname.endswith(".json"):
            with open(f"{stages_dir}/{fname}") as f:
                stages[fname.replace(".json","")] = json.load(f)

    # Run enrichment
    from data_enrichment import enrich_all
    urls = [url]
    # Get live URLs from sitemap (skip broken links from findings)
    sitemap_url = url.rstrip("/") + "/sitemap.xml"
    try:
        with httpx.Client(timeout=10, follow_redirects=True) as c:
            r = c.get(sitemap_url)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for tag in [".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc", ".//loc"]:
                for loc in root.findall(tag):
                    u = loc.text.strip() if loc.text else ""
                    if u.startswith(url) and u not in urls:
                        urls.append(u)
    except Exception:
        pass
    # Always include key solution pages (sitemaps often miss them)
    for path in ["/solutions-should-cost-modeling","/solutions-pcf-reporting",
                 "/solutions-tariff-analysis","/industries-electronics",
                 "/blog","/stories","/build-a-product-model","/about"]:
        u = url.rstrip("/") + path
        if u not in urls:
            urls.append(u)

    # Prioritize solution pages, then include up to 20 total
    priority = [u for u in urls if any(p in u for p in ["solution","industries","build","about","blog","stories"])]
    rest = [u for u in urls if u not in priority]
    enrichment = enrich_all(url, (priority + rest)[:30])
    print(f"Enrichment: {enrichment['summary']['total_pages']} pages")

    # Build context
    from unified_runner import contextualize_output
    ctx = contextualize_output(latest, url)

    # Collect findings from all stages
    from output_enhancements import collect_all_findings, build_output_summary
    all_findings = collect_all_findings(stages)

    # Add enrichment-based findings
    summary = enrichment.get("summary", {})
    # Schema quality finding
    pages_with_schema = summary.get("pages_with_schema", 0)
    pages_total = summary.get("total_pages", 1)
    if pages_with_schema < pages_total:
        all_findings.append({
            "stage_name": "enrichment", "rule_id": "schema_validation", "layer": "L1", "category": "A",
            "severity": "high", "certainty": "confirmed",
            "title": f"Schema missing on {pages_total - pages_with_schema} of {pages_total} pages",
            "what_it_improves": "AI content parsing, rich snippets, Knowledge Panel",
            "effort": 2, "priority": 15.0,
        })
    # FAQ quality finding
    faq_scores = enrichment.get("faq_quality", {})
    if faq_scores:
        avg_faq = sum(q.get("score", 0) for q in faq_scores.values()) / len(faq_scores)
        if avg_faq < 6:
            all_findings.append({
                "stage_name": "enrichment", "rule_id": "content_quality", "layer": "L2", "category": "B",
                "severity": "medium", "certainty": "confirmed",
                "title": f"FAQ quality low ({avg_faq:.1f}/10) — answers need more specificity",
                "what_it_improves": "AI citation rate, user engagement, conversion",
                "effort": 2, "priority": 10.0,
            })
    # Caching finding
    if summary.get("has_caching_pct", 0) == 0:
        all_findings.append({
            "stage_name": "enrichment", "rule_id": "lcp_slow", "layer": "L1", "category": "B",
            "severity": "medium", "certainty": "confirmed",
            "title": "Zero caching headers — all assets re-downloaded on every visit",
            "what_it_improves": "Page speed, user experience, Core Web Vitals",
            "effort": 1, "priority": 12.0,
        })

    # Generate L3 findings from platform data
    ext = stages.get("external_presence", {})
    platforms = ext.get("platforms", {})
    for pname, pdata in platforms.items():
        s = pdata.get("score", 0)
        if s == 0:
            rule = {"G2": "missing_g2", "Capterra": "missing_capterra", "YouTube": "missing_youtube",
                    "Reddit": "missing_reddit", "Wikipedia": "no_wikipedia"}.get(pname, "missing_platform")
            all_findings.append({
                "stage_name": "external_presence", "rule_id": rule, "layer": "L3", "category": "A",
                "severity": "high", "certainty": "confirmed",
                "title": f"No {pname} presence — {pdata.get('missed_opportunity','Missing critical visibility surface')[:100]}",
                "what_it_improves": "AI citation rate, branded search, buyer trust",
                "effort": 1, "priority": 20.0,
            })
        elif s < 5:
            all_findings.append({
                "stage_name": "external_presence", "rule_id": f"low_{pname.lower()}_quality", "layer": "L3", "category": "B",
                "severity": "medium", "certainty": "confirmed",
                "title": f"{pname} quality low ({s}/10) — {pdata.get('recommendation','')[:100]}",
                "what_it_improves": "AI citation rate, branded search, buyer trust",
                "effort": 2, "priority": 10.0,
            })

    # Generate findings from enrichment summary — every failing binary gate becomes an action
    summary = enrichment.get("summary", {})
    total = summary.get("total_pages", 1)

    def _add_finding(rule_id, layer, cat, severity, title, improves, effort, priority):
        all_findings.append({"stage_name":"enrichment","rule_id":rule_id,"layer":layer,"category":cat,
            "severity":severity,"certainty":"confirmed","title":title,"what_it_improves":improves,
            "effort":effort,"priority":priority})

    # L1 binary gates that fail
    if summary.get("has_canonical_pct", 1) < 0.8:
        _add_finding("canonical_url", "L1", "A", "medium", "Canonical URLs missing on some pages", "Duplicate content prevention, crawl efficiency", 1, 12.0)
    if summary.get("has_breadcrumb_pct", 1) < 0.5:
        _add_finding("breadcrumb", "L1", "A", "medium", "Breadcrumb navigation missing on pages", "Site structure clarity, rich results", 2, 10.0)
    if summary.get("has_headings_pct", 1) < 0.8:
        _add_finding("heading_hierarchy", "L1", "A", "medium", f"Heading hierarchy issues on {total - int(total*summary.get('has_headings_pct',0))} pages", "Content structure, AI citation odds", 2, 11.0)
    if summary.get("single_h1_pct", 1) < 0.8:
        _add_finding("single_h1", "L1", "A", "low", f"Multiple H1s found on pages", "SEO best practice, content clarity", 1, 9.0)
    if summary.get("has_caching_pct", 0) == 0:
        _add_finding("caching", "L1", "B", "medium", "No caching headers on any page", "Page speed, Core Web Vitals, user experience", 1, 12.0)
    if summary.get("alt_text_pct", 1) < 0.8:
        _add_finding("alt_text", "L1", "B", "low", f"Image alt text missing on {int(total*(1-summary.get('alt_text_pct',1)))} pages", "Accessibility, SEO, image search", 1, 8.0)

    # L2 binary gates that fail
    if summary.get("has_author_pct", 1) < 0.5:
        _add_finding("author_bios", "L2", "A", "medium", f"Author bios missing on {int(total*(1-summary.get('has_author_pct',1)))} pages", "E-E-A-T credibility, AI trust signals", 1, 11.0)
    if summary.get("has_credentials_pct", 1) < 0.5:
        _add_finding("author_credentials", "L2", "A", "medium", "Author credentials missing", "E-E-A-T expertise signals", 1, 10.0)
    if summary.get("has_external_sources_pct", 1) < 0.5:
        _add_finding("external_sources", "L2", "A", "medium", "External sources not cited on most pages", "AI trust, credibility, backlink generation", 2, 10.0)
    if summary.get("has_last_updated_pct", 1) < 0.5:
        _add_finding("last_updated", "L2", "A", "medium", "Last-updated dates missing", "Content freshness signals, AI citation weight", 1, 11.0)
    if summary.get("has_original_data_pct", 1) < 0.3:
        _add_finding("original_data", "L2", "B", "medium", "No original data or research on pages", "AI citation rate, backlink generation, authority", 3, 9.0)
    if summary.get("has_lists_pct", 1) < 0.3:
        _add_finding("lists", "L2", "A", "low", "Bulleted/numbered lists missing from pages", "Content scannability, AI citation patterns", 1, 8.0)
    if summary.get("has_case_study_pct", 1) < 0.3:
        _add_finding("case_studies", "L2", "A", "high", "No case studies found on site", "Buyer social proof, AI authority signals", 3, 12.0)

    # FAQ quality (already generated above if faq_scores exist)

    ctx["all_findings"] = all_findings
    ctx["enrichment"] = enrichment
    ctx["audit_id"] = latest.split("/")[-1]

    # Build summary
    ctx = build_output_summary(ctx, all_findings)

    # Generate HTML
    from report_full import render_full_html
    html_path = f"{latest}/v1/trellace-report.html"
    render_full_html(ctx, html_path)
    print(f"HTML: {html_path}")
    print(f"Findings: {len(all_findings)}, Actions per layer: L1={len([f for f in all_findings if f.get('layer')=='L1'])} L2={len([f for f in all_findings if f.get('layer')=='L2'])} L3={len([f for f in all_findings if f.get('layer')=='L3'])}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
