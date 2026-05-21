#!/usr/bin/env python3
"""
Trellace Visibility Audit — One-click runner.

Usage:
    python3 run_audit.py https://www.muir.ai                        # basic
    python3 run_audit.py https://www.muir.ai --name "Muir AI"        # with client name
    python3 run_audit.py https://www.muir.ai --competitors apriori.com,galorath.com

Output: audits/{id}/v1/trellace-report.html — standalone, client-ready.
"""
import os, sys, json, time, argparse

# Auto-detect API keys
os.environ.setdefault("ANTHROPIC_API_KEY", os.environ.get("TRELLACE_ANTHROPIC_API_KEY", ""))
os.environ.setdefault("OPENAI_API_KEY", os.environ.get("TRELLACE_OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "")))
os.environ.setdefault("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

# Load .env keys if present
try:
    with open(".env") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                v = v.strip().strip('"').strip("'")
                if k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CLICKUP_API_KEY") and v:
                    os.environ.setdefault(k, v)
except Exception:
    pass

sys.path.insert(0, "context/knowledge/visibility-framework")

def main():
    parser = argparse.ArgumentParser(description="Trellace Visibility Audit")
    parser.add_argument("url", help="Target URL to audit")
    parser.add_argument("--name", default="", help="Client/brand name")
    parser.add_argument("--description", default="", help="One-line product description")
    parser.add_argument("--competitors", default="", help="Comma-separated competitor URLs")
    parser.add_argument("--type", default="b2b_saas", choices=["b2b_saas","b2b_services","dtc","consumer"])
    parser.add_argument("--pages", type=int, default=6, help="Max content pages to score")
    parser.add_argument("--no-l4", action="store_true", help="Skip AI visibility polling (faster)")
    args = parser.parse_args()

    from unified_runner import setup_pipeline, build_context
    from auditstack.orchestrator import Pipeline
    from auditstack.registry import REGISTRY
    from l4_multimodel import patch_for_multimodel

    competitors = [c.strip() for c in args.competitors.split(",") if c.strip()]
    if not args.name:
        args.name = args.url.replace("https://","").replace("www.","").split("/")[0]

    print(f"\n  Trellace Visibility Audit: {args.url}")
    print(f"  {'='*50}\n")

    t0 = time.time()

    # Setup pipeline
    run_args = {"url": args.url, "name": args.name, "description": args.description,
                "competitors": competitors, "type": args.type, "max_pages": args.pages,
                "gsc_secret": None, "output_dir": "./audits", "disable": []}
    setup_pipeline(run_args)

    if not args.no_l4:
        print("  L4: Multi-model AI visibility polling enabled")
        patch_for_multimodel()

    ctx = build_context(run_args)
    result = Pipeline().run(ctx)
    audit_time = time.time() - t0

    # Find output
    import glob
    audit_dirs = sorted([d for d in os.listdir("audits") if os.path.isdir(f"audits/{d}")], reverse=True)
    latest = f"audits/{audit_dirs[0]}"

    # Run enrichment
    print("  Running enrichment...")
    from data_enrichment import enrich_all
    import httpx, xml.etree.ElementTree as ET
    urls = [args.url]
    try:
        sitemap_url = args.url.rstrip("/") + "/sitemap.xml"
        with httpx.Client(timeout=10, follow_redirects=True) as c:
            r = c.get(sitemap_url)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            for tag in [".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc", ".//loc"]:
                for loc in root.findall(tag):
                    u = loc.text.strip() if loc.text else ""
                    if u.startswith(args.url) and u not in urls:
                        urls.append(u)
    except Exception:
        pass
    for path in ["/solutions-should-cost-modeling","/solutions-pcf-reporting",
                 "/solutions-tariff-analysis","/industries-electronics",
                 "/blog","/stories","/build-a-product-model","/about"]:
        u = args.url.rstrip("/") + path
        if u not in urls: urls.append(u)
    priority = [u for u in urls if any(p in u for p in ["solution","industries","build","about","blog","stories"])]
    rest = [u for u in urls if u not in priority]
    enrichment = enrich_all(args.url, (priority + rest)[:30])

    # Build report
    print("  Generating report...")
    from unified_runner import contextualize_output
    ctx = contextualize_output(latest, args.url)

    # Collect findings
    stages_dir = f"{latest}/v1/stages"
    stages = {}
    for fname in os.listdir(stages_dir):
        if fname.endswith(".json"):
            with open(f"{stages_dir}/{fname}") as f:
                stages[fname.replace(".json","")] = json.load(f)

    from output_enhancements import collect_all_findings, build_output_summary
    all_findings = collect_all_findings(stages)

    # Add enrichment findings
    summary = enrichment.get("summary", {})
    total = summary.get("total_pages", 1)
    def _af(rid, layer, cat, severity, title, improves, effort, priority):
        all_findings.append({"stage_name":"enrichment","rule_id":rid,"layer":layer,"category":cat,
            "severity":severity,"certainty":"confirmed","title":title,"what_it_improves":improves,
            "effort":effort,"priority":priority})

    if summary.get("pages_with_schema",0) < total:
        _af("schema_validation","L1","A","high",f"Schema missing on {total-summary['pages_with_schema']} pages","AI parsing, rich snippets, Knowledge Panel",2,15.0)
    if summary.get("has_caching_pct",0) == 0:
        _af("caching","L1","B","medium","No caching headers on any page","Page speed, Core Web Vitals",1,12.0)
    faq_scores = enrichment.get("faq_quality",{})
    if faq_scores:
        avg = sum(q.get("score",0) for q in faq_scores.values())/len(faq_scores)
        if avg < 6:
            _af("content_quality","L2","B","medium",f"FAQ quality low ({avg:.1f}/10)","AI citation rate, user engagement",2,10.0)
    ext = stages.get("external_presence",{})
    for pname, pdata in ext.get("platforms",{}).items():
        s = pdata.get("score",0)
        if s == 0:
            _af(f"missing_{pname.lower()}","L3","A","high",f"No {pname} presence","AI citation rate, branded search",1,20.0)
        elif s < 5:
            _af(f"low_{pname.lower()}_quality","L3","B","medium",f"{pname} quality low ({s}/10)","AI citation rate, buyer trust",2,10.0)

    ctx["all_findings"] = all_findings
    ctx["enrichment"] = enrichment
    ctx["audit_id"] = latest.split("/")[-1]
    ctx = build_output_summary(ctx, all_findings)

    # Render HTML
    from report_full import render_full_html
    html_path = f"{latest}/v1/trellace-report.html"
    render_full_html(ctx, html_path)

    total_time = time.time() - t0
    print(f"\n  {'='*50}")
    print(f"  Composite: {ctx.get('composite','?')}/100")
    print(f"  HTML: {html_path}")
    print(f"  Time: {total_time:.0f}s (audit: {audit_time:.0f}s + enrichment + report)")
    print(f"  Findings: {len(all_findings)} across L1/L2/L3")
    print()

    # Open in browser
    import subprocess
    subprocess.run(["open", html_path])

if __name__ == "__main__":
    main()
