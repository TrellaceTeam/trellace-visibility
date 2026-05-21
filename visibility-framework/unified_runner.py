"""
Unified audit runner — all 4 layers, contextual output.
Makes sure every score means something.
"""
import importlib.util, sys, json, os, time
from datetime import datetime

# Load our custom stages
for name, fpath in [
    ("content_stage_v2", "context/knowledge/visibility-framework/content_stage_v2.py"),
    ("layer3_stage", "context/knowledge/visibility-framework/layer3_stage.py"),
]:
    spec = importlib.util.spec_from_file_location(name, fpath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)

from auditstack.context import AuditContext, ClientType, GoogleOAuthScopes
from auditstack.orchestrator import Pipeline
from auditstack.registry import REGISTRY
from auditstack.cli import _register_bundled_stages
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

from content_stage_v2 import ContentStageV2
from layer3_stage import ExternalPresenceStage

os.environ.setdefault("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")


def get_gsc_token(secret_file: str) -> str:
    SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
    cache = "gsc_token.pickle"
    creds = None
    if os.path.exists(cache):
        with open(cache, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(cache, "wb") as f:
            pickle.dump(creds, f)
    creds.refresh(Request())
    return creds.token


def build_context(args: dict) -> AuditContext:
    google_oauth = None
    if args.get("gsc_secret"):
        try:
            token = get_gsc_token(args["gsc_secret"])
            google_oauth = GoogleOAuthScopes(gsc=True, access_token=token)
        except Exception as e:
            print(f"  GSC auth skipped: {e}")

    return AuditContext(
        target_url=args["url"],
        client_name=args.get("name", ""),
        client_description=args.get("description", ""),
        client_type=ClientType[args.get("type", "B2B_SAAS").upper()],
        competitors=args.get("competitors", []),
        google_oauth=google_oauth,
        persistence_root=args.get("output_dir", "./audits"),
    )


def setup_pipeline(args: dict):
    REGISTRY.clear()
    _register_bundled_stages()

    # Replace stages with our versions. Keep entity for dependency chain.
    REGISTRY.unregister("content")
    REGISTRY.register(ContentStageV2(max_pages=args.get("max_pages", 8)))
    REGISTRY.register(ExternalPresenceStage())

    # Enable/disable stages based on config
    for name in args.get("disable", []):
        REGISTRY.unregister(name)


def contextualize_output(audit_dir: str, url: str = "") -> dict:
    """Turn raw audit output into contextual, meaningful scores. Reads from stage files."""
    stages = {}
    stages_dir = f"{audit_dir}/v1/stages"
    if os.path.exists(stages_dir):
        for fname in os.listdir(stages_dir):
            if fname.endswith(".json"):
                stage_name = fname.replace(".json", "")
                with open(f"{stages_dir}/{fname}") as f:
                    stages[stage_name] = json.load(f)

    ctx = {}

    # ── L1: Technical ──
    tech = stages.get("technical", {})
    if tech:
        cwv = tech.get("core_web_vitals", {})
        robots = tech.get("robots_txt_summary", {})
        schema_count = len(tech.get("schema_types_found", []))
        ctx["l1"] = {
            "score": tech.get("layer_score"),
            "pages_crawled": tech.get("pages_crawled"),
            "broken_links": len(tech.get("broken_links", [])),
            "broken_urls": tech.get("broken_links", [])[:10],
            "schema_types": schema_count,
            "lcp_ms": cwv.get("lcp_ms"),
            "cls": cwv.get("cls"),
            "accessibility": cwv.get("accessibility"),
            "performance": cwv.get("performance"),
            "seo_score": cwv.get("seo"),
            "robots_disallows": len(robots.get("disallows", [])),
            "meaning": _l1_meaning(tech),
        }

    # ── L2: Content ──
    content = stages.get("content", {})
    if content:
        pages = content.get("per_page_scores", [])
        ctx["l2"] = {
            "score": content.get("layer_score"),
            "pages_analyzed": content.get("pages_analyzed"),
            "avg_citability": content.get("avg_citability"),
            "avg_flesch": content.get("avg_flesch"),
            "best_page": _best_page(pages),
            "worst_page": _worst_page(pages),
            "pages": pages,
            "meaning": _l2_meaning(content),
        }

    # ── L3: External ──
    ext = stages.get("external_presence", {})
    if ext:
        platforms = ext.get("platforms", {})
        ctx["l3"] = {
            "score": ext.get("layer_score"),
            "strongest": _strongest_platform(platforms),
            "weakest": _weakest_platform(platforms),
            "missing": [p for p, d in platforms.items() if d.get("score", 0) == 0],
            "platforms": platforms,
            "meaning": _l3_meaning(ext),
        }

    # ── L4: AI Visibility ──
    ai = stages.get("ai_retrieval", {})
    if ai:
        sov = ai.get("sov_by_platform", {})
        ctx["l4"] = {
            "score": ai.get("layer_score"),
            "sov": sov,
            "sov_raw": sov,
            "competitors": ai.get("competitor_sov", {}),
            "meaning": _l4_meaning(ai),
        }

    # ── Overall ──
    scores = [ctx[k]["score"] for k in ["l1","l2","l3","l4"] if k in ctx and ctx[k]["score"] is not None]
    ctx["composite"] = round(sum(scores) / len(scores)) if scores else 0
    ctx["audit_id"] = audit_dir.split("/")[-1]
    ctx["url"] = url

    return ctx


def _l1_meaning(tech: dict) -> str:
    cwv = tech.get("core_web_vitals", {})
    lcp = cwv.get("lcp_ms", 0) or 0
    cls = cwv.get("cls", 0) or 0
    broken = len(tech.get("broken_links", []))
    schema = len(tech.get("schema_types_found", []))
    parts = []
    if lcp > 4000:
        parts.append(f"LCP of {lcp/1000:.1f}s is 7x the 2.5s target")
    if cls and cls > 0.1:
        parts.append(f"CLS of {cls:.3f} exceeds 0.1 threshold")
    if broken:
        parts.append(f"{broken} broken links wasting crawl budget")
    if schema == 0:
        parts.append("zero schema types — AI cannot parse your content structure")
    return ". ".join(parts) if parts else "Technical foundation is solid"


def _l2_meaning(content: dict) -> str:
    cit = content.get("avg_citability", 0)
    fl = content.get("avg_flesch", 0)
    pages = content.get("pages_analyzed", 0)
    parts = []
    if cit < 4:
        parts.append(f"avg citability {cit:.1f}/10 — most content invisible to AI retrieval")
    elif cit < 6:
        parts.append(f"avg citability {cit:.1f}/10 — some pages citable, others need work")
    else:
        parts.append(f"avg citability {cit:.1f}/10 — strong, most content AI-ready")
    if fl < 30:
        parts.append(f"Flesch {fl:.0f} is very complex for B2B (target: 60-70)")
    elif fl < 50:
        parts.append(f"Flesch {fl:.0f} is complex (target: 60-70)")
    return f"{pages} pages analyzed. " + ". ".join(parts)


def _l3_meaning(ext: dict) -> str:
    plats = ext.get("platforms", {})
    strong = [p for p, d in plats.items() if d.get("score", 0) >= 6]
    missing = [p for p, d in plats.items() if d.get("score", 0) == 0]
    parts = []
    if strong:
        parts.append(f"strong on {', '.join(strong)}")
    if missing:
        parts.append(f"missing from {', '.join(missing)} — {'AI citation gates' if 'G2' in missing or 'Capterra' in missing else 'key visibility surfaces'}")
    return ". ".join(parts) if parts else "External presence needs development across all platforms"


def _l4_meaning(ai: dict) -> str:
    sov = ai.get("sov_by_platform", {})
    if not sov:
        return "AI polling not configured — needs Perplexity API key"
    total = sum(sov.values())
    if total == 0:
        return "Zero Share of Voice across all AI platforms — brand is invisible to AI"
    best_platform = max(sov.items(), key=lambda x: x[1]) if sov else ("none", 0)
    return f"Best platform: {best_platform[0]} at {best_platform[1]*100:.0f}% SOV. AI discovery calls estimated at ~{int(total*100)}% of AI referral traffic."


def _best_page(pages: list) -> dict:
    if not pages:
        return {}
    return max(pages, key=lambda p: p.get("page_score", 0))


def _worst_page(pages: list) -> dict:
    if not pages:
        return {}
    return min(pages, key=lambda p: p.get("page_score", 0))


def _strongest_platform(platforms: dict) -> str:
    if not platforms:
        return "none"
    return max(platforms.items(), key=lambda x: x[1].get("score", 0))[0]


def _weakest_platform(platforms: dict) -> str:
    scored = {p: d for p, d in platforms.items() if d.get("score", 0) > 0}
    if not scored:
        return "all equal"
    return min(scored.items(), key=lambda x: x[1].get("score", 0))[0]


def print_report(ctx: dict):
    """Print a human-readable audit report with contextual scores."""
    print(f"\n{'='*70}")
    print(f"  VISIBILITY AUDIT: {ctx.get('url', '')}")
    print(f"  Audit ID: {ctx['audit_id']}")
    print(f"  Composite Score: {ctx['composite']}/100")
    print(f"  🟢 A (binary gates): {ctx.get('binary_gates', 0)}  |  🔵 B (scalar issues): {ctx.get('scalar_issues', 0)}")
    print(f"{'='*70}")

    for key in ["l1", "l2", "l3", "l4"]:
        data = ctx.get(key, {})
        if not data:
            continue
        labels = {"l1": "LAYER 1 — Technical Foundation",
                  "l2": "LAYER 2 — Content Citability",
                  "l3": "LAYER 3 — External Presence",
                  "l4": "LAYER 4 — AI Visibility"}
        print(f"\n  {labels[key]}")
        print(f"  Score: {data.get('score', 'N/A')}/100")
        print(f"  {data.get('meaning', '')}")

        if key == "l2":
            best = data.get("best_page", {})
            worst = data.get("worst_page", {})
            if best:
                print(f"  Best page:  {best.get('url','')[-60:]} ({best.get('page_score','')})")
            if worst:
                print(f"  Worst page: {worst.get('url','')[-60:]} ({worst.get('page_score','')})")

        if key == "l3":
            print(f"  Strongest: {data.get('strongest','')}")
            missing = data.get("missing", [])
            if missing:
                print(f"  Missing:   {', '.join(missing)}")

        if key == "l4":
            sov = data.get("sov", {})
            if sov:
                for platform, s in sov.items():
                    print(f"  {platform}: {s*100:.0f}% SOV")

    # ── Priority Ranking ──
    top = ctx.get("top_findings", [])
    if top:
        print(f"\n{'='*70}")
        print(f"  TOP PRIORITY ACTIONS (ranked by impact ÷ effort)")
        print(f"{'='*70}")
        for f in top:
            cat = f.get("category", "?")
            cat_icon = "🟢" if cat == "A" else "🔵"
            print(f"  #{f['rank']} {cat_icon} [{cat}] [{f['layer']}] {f['title'][:90]}")
            print(f"     Priority: {f['priority']} | Effort: {f['effort']}/5 | Improves: {f['what_it_improves']}")

    # ── Remediation Drafts ──
    rems = ctx.get("remediations", [])
    if rems:
        print(f"\n{'='*70}")
        print(f"  CONTENT FIXES (LLM-generated drafts)")
        print(f"{'='*70}")
        for r in rems:
            print(f"  Fixing: {r['for']}")
            print(f"  → {r['draft'][:200]}")
            if r.get("explanation"):
                print(f"  Reason: {r['explanation'][:150]}")
            print()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--name", default="")
    parser.add_argument("--description", default="")
    parser.add_argument("--competitors", default="")
    parser.add_argument("--type", default="b2b_saas")
    parser.add_argument("--gsc-secret", default=None)
    parser.add_argument("--max-pages", type=int, default=6)
    parser.add_argument("--fast", action="store_true", help="Skip heavy layers for speed")
    args = parser.parse_args()

    run_args = {
        "url": args.url,
        "name": args.name,
        "description": args.description,
        "competitors": [c.strip() for c in args.competitors.split(",") if c.strip()],
        "type": args.type,
        "gsc_secret": args.gsc_secret,
        "max_pages": args.max_pages,
        "output_dir": "./audits",
        "disable": [],
    }
    # Set up API keys
    os.environ.setdefault("ANTHROPIC_API_KEY", os.environ.get("TRELLACE_ANTHROPIC_API_KEY", ""))
    os.environ.setdefault("OPENAI_API_KEY", os.environ.get("TRELLACE_OPENAI_API_KEY", os.environ.get("OPENAI_API_KEY", "")))
    os.environ.setdefault("DEEPSEEK_KEY", "sk-0d31b1d5c7a64b48ac945e5991578e2e")

    if args.fast:
        run_args["disable"] = []
    else:
        run_args["disable"] = []

    print(f"Starting audit: {args.url}\n")
    t0 = time.time()

    setup_pipeline(run_args)

    # L4 Multi-model polling (industry standard)
    from l4_multimodel import patch_for_multimodel
    patch_for_multimodel()

    # Run data enrichment (per-page checks)
    from data_enrichment import enrich_all
    import xml.etree.ElementTree as ET
    page_urls = [args.url]
    try:
        sitemap_url = args.url.rstrip("/") + "/sitemap.xml"
        with httpx.Client(timeout=10, follow_redirects=True) as c:
            r = c.get(sitemap_url)
        if r.status_code == 200:
            root = ET.fromstring(r.text)
            # Try multiple namespace patterns
            for ns_name in ["ns", ""]:
                ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"} if ns_name == "ns" else {}
                tag = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc" if not ns else ".//ns:loc"
                for loc in root.findall(tag, ns) if "{http" in tag else root.findall(".//loc"):
                    u = loc.text.strip() if loc.text else ""
                    if u.startswith(args.url) and u not in page_urls:
                        page_urls.append(u)
                if len(page_urls) > 5: break
    except Exception:
        pass
    # Fallback: add key pages if sitemap gave nothing
    if len(page_urls) < 3:
        for path in ["/solutions-should-cost-modeling","/solutions-pcf-reporting",
                     "/solutions-tariff-analysis","/industries-electronics","/stories","/blog",
                     "/blog-posts/navigating-cbams-rising-costs-through-smart-supply-chain-optimization"]:
            u = args.url.rstrip("/") + path
            if u not in page_urls: page_urls.append(u)
    enrichment = enrich_all(args.url, page_urls[:20])
    s = enrichment.get("summary", {})
    print(f"  Enrichment: {s.get('total_pages',0)} pages, llms_txt={enrichment['llms_txt']['exists']}, schema={s.get('pages_with_schema',0)}/{s.get('total_pages',0)}, faq={s.get('pages_with_faq',0)}, eeat={len(enrichment.get('eeat',{}))}")

    ctx = build_context(run_args)
    result = Pipeline().run(ctx)
    elapsed = time.time() - t0

    # Read from latest audit (newest by modification time)
    audit_dirs = sorted(
        [d for d in os.listdir("audits") if os.path.isdir(f"audits/{d}") and os.path.exists(f"audits/{d}/v1/stages")],
        key=lambda d: os.path.getmtime(f"audits/{d}"), reverse=True
    )
    latest_dir = f"audits/{audit_dirs[0]}"
    contextual = contextualize_output(latest_dir, args.url)
    contextual["enrichment"] = enrichment  # pass enrichment data to report
    print(f"  Reading from: {latest_dir}")
    # Enhance with priority ranking, A/B/C, remediations
    from output_enhancements import collect_all_findings, build_output_summary
    all_stages = {}
    stages_dir = f"{latest_dir}/v1/stages"
    if os.path.exists(stages_dir):
        for fname in os.listdir(stages_dir):
            if fname.endswith(".json"):
                stage_name = fname.replace(".json", "")
                with open(f"{stages_dir}/{fname}") as f:
                    all_stages[stage_name] = json.load(f)

    all_findings = collect_all_findings(all_stages)
    contextual = build_output_summary(contextual, all_findings)
    contextual["all_findings"] = all_findings

    print_report(contextual)

    # Generate comprehensive HTML report
    from report_full import render_full_html
    html_path = f"{latest_dir}/v1/trellace-report.html"
    render_full_html(contextual, html_path)
    print(f"\n  HTML report: {html_path}")
    print(f"  Total time: {elapsed:.0f}s")

if __name__ == "__main__":
    main()
