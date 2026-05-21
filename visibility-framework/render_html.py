"""Generate a standalone HTML report from unified audit output."""
import json, os

def render_html(ctx: dict, output_path: str):
    l1 = ctx.get("l1", {})
    l2 = ctx.get("l2", {})
    l3 = ctx.get("l3", {})
    l4 = ctx.get("l4", {})
    top = ctx.get("top_findings", [])
    rems = ctx.get("remediations", [])

    def score_color(s):
        if s is None: return "#9ca3af", "?"
        if s >= 80: return "#059669", "A"
        if s >= 60: return "#2563eb", "B"
        if s >= 40: return "#ca8a04", "C"
        if s >= 20: return "#ea580c", "D"
        return "#dc2626", "F"

    l1_color, l1_grade = score_color(l1.get("score"))
    l2_color, l2_grade = score_color(l2.get("score"))
    l3_color, l3_grade = score_color(l3.get("score"))
    comp_color, comp_grade = score_color(ctx.get("composite"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Visibility Audit — {ctx.get('url', '')}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; color: #1e293b; line-height:1.6; }}
.container {{ max-width:900px; margin:0 auto; padding:24px; }}
.header {{ background:#fff; border-radius:12px; padding:32px; margin-bottom:24px; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
.header h1 {{ font-size:1.5rem; color:#64748b; font-weight:400; }}
.header .url {{ font-size:2rem; font-weight:700; color:#0f172a; margin:4px 0; }}
.scores {{ display:flex; gap:16px; margin-top:24px; flex-wrap:wrap; }}
.score-card {{ flex:1; min-width:140px; background:#f1f5f9; border-radius:10px; padding:16px; text-align:center; }}
.score-card .label {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.05em; color:#64748b; margin-bottom:8px; }}
.score-card .number {{ font-size:2.5rem; font-weight:700; }}
.score-card .grade {{ font-size:.85rem; margin-top:4px; font-weight:600; }}
.layer {{ background:#fff; border-radius:12px; padding:24px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
.layer h2 {{ font-size:1.1rem; color:#0f172a; }}
.layer .layer-score {{ display:inline-block; padding:4px 12px; border-radius:6px; font-weight:700; font-size:.9rem; margin-bottom:12px; }}
.layer .meaning {{ color:#475569; font-size:.95rem; margin-bottom:12px; }}
.layer .detail {{ font-size:.85rem; color:#64748b; }}
.findings {{ background:#fff; border-radius:12px; padding:24px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
.findings h2 {{ font-size:1.1rem; margin-bottom:16px; }}
.finding {{ padding:12px 0; border-bottom:1px solid #e2e8f0; }}
.finding:last-child {{ border-bottom:0; }}
.finding .rank {{ display:inline-block; width:28px; height:28px; line-height:28px; text-align:center; border-radius:6px; font-weight:700; font-size:.85rem; background:#0f172a; color:#fff; margin-right:8px; }}
.finding .cat {{ display:inline-block; padding:1px 8px; border-radius:4px; font-size:.75rem; font-weight:600; margin-right:8px; }}
.cat-A {{ background:#dcfce7; color:#166534; }}
.cat-B {{ background:#dbeafe; color:#1e40af; }}
.finding .title {{ font-weight:600; }}
.finding .meta {{ font-size:.8rem; color:#64748b; margin-top:4px; }}
.remediations {{ background:#fff; border-radius:12px; padding:24px; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,.1); }}
.remediations h2 {{ font-size:1.1rem; margin-bottom:16px; }}
.rem {{ padding:12px 0; border-bottom:1px solid #e2e8f0; }}
.rem:last-child {{ border-bottom:0; }}
.rem .fixing {{ font-weight:600; font-size:.85rem; color:#64748b; margin-bottom:4px; }}
.rem .draft {{ font-size:.95rem; color:#0f172a; padding:8px 12px; background:#f0fdf4; border-left:3px solid #22c55e; border-radius:4px; margin:8px 0; }}
.rem .reason {{ font-size:.8rem; color:#64748b; }}
.footer {{ text-align:center; padding:24px; color:#94a3b8; font-size:.8rem; }}
</style>
</head>
<body>
<div class="container">

<div class="header">
<h1>VISIBILITY AUDIT</h1>
<div class="url">{ctx.get('url', '')}</div>
<div class="scores">
<div class="score-card">
<div class="label">Composite</div>
<div class="number" style="color:{comp_color}">{ctx.get('composite', '?')}</div>
<div class="grade" style="color:{comp_color}">Grade {comp_grade}</div>
</div>
<div class="score-card">
<div class="label">L1 Technical</div>
<div class="number" style="color:{l1_color}">{l1.get('score', '?')}</div>
<div class="grade" style="color:{l1_color}">Grade {l1_grade}</div>
</div>
<div class="score-card">
<div class="label">L2 Content</div>
<div class="number" style="color:{l2_color}">{l2.get('score', '?')}</div>
<div class="grade" style="color:{l2_color}">Grade {l2_grade}</div>
</div>
<div class="score-card">
<div class="label">L3 External</div>
<div class="number" style="color:{l3_color}">{l3.get('score', '?')}</div>
<div class="grade" style="color:{l3_color}">Grade {l3_grade}</div>
</div>
</div>
</div>

<div class="layer">
<h2>🔧 Layer 1 — Technical Foundation</h2>
<div class="layer-score" style="background:{l1_color}20;color:{l1_color}">{l1.get('score', '?')}/100</div>
<div class="meaning">{l1.get('meaning', '')}</div>
<div class="detail">Pages crawled: {l1.get('pages_crawled', '?')} · Broken links: {l1.get('broken_links', '?')} · Schema types: {l1.get('schema_types', '?')} · LCP: {l1.get('lcp_ms') or '?'}ms · CLS: {l1.get('cls') or '?'}</div>
</div>

<div class="layer">
<h2>📝 Layer 2 — Content Citability</h2>
<div class="layer-score" style="background:{l2_color}20;color:{l2_color}">{l2.get('score', '?')}/100</div>
<div class="meaning">{l2.get('meaning', '')}</div>"""

    if l2.get("best_page"):
        bp = l2["best_page"]
        html += f'<div class="detail">Best page: {bp.get("url","")[-50:]} ({bp.get("page_score","")}) · Worst page: {l2.get("worst_page",{}).get("url","")[-50:] if l2.get("worst_page") else ""} ({l2.get("worst_page",{}).get("page_score","") if l2.get("worst_page") else ""})</div>'

    html += f"""
</div>

<div class="layer">
<h2>🌐 Layer 3 — External Presence</h2>
<div class="layer-score" style="background:{l3_color}20;color:{l3_color}">{l3.get('score', '?')}/100</div>
<div class="meaning">{l3.get('meaning', '')}</div>
<div class="detail">Strongest: {l3.get('strongest','')} · Missing: {', '.join(l3.get('missing',[]))}</div>
</div>"""

    if top:
        html += '<div class="findings"><h2>📋 Top Priority Actions</h2>'
        for f in top:
            cat = f.get("category", "B")
            html += f"""<div class="finding">
<span class="rank">{f['rank']}</span>
<span class="cat cat-{cat}">{cat} — {f.get('layer','?')}</span>
<span class="title">{f['title'][:120]}</span>
<div class="meta">Priority: {f['priority']} · Effort: {f.get('effort','?')}/5 · Improves: {f.get('what_it_improves','')}</div>
</div>"""
        html += '</div>'

    if rems:
        html += '<div class="remediations"><h2>✏️ Content Fixes (LLM-generated)</h2>'
        for r in rems:
            html += f"""<div class="rem">
<div class="fixing">Fixing: {r.get('for','')}</div>
<div class="draft">{r.get('draft','')}</div>
<div class="reason">{r.get('explanation','')}</div>
</div>"""
        html += '</div>'

    html += f"""
<div class="footer">
Trellace Visibility Framework v2 · Audit ID: {ctx.get('audit_id','')} · Generated {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
</div>
</div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    return output_path
