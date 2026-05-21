"""Debug FAQ data flow."""
import sys
sys.path.insert(0, 'context/knowledge/visibility-framework')
from data_enrichment import enrich_all

url = 'https://www.muir.ai'
paths = ["/solutions-should-cost-modeling", "/solutions-pcf-reporting",
         "/solutions-tariff-analysis", "/industries-electronics",
         "/blog", "/stories", "/build-a-product-model"]
urls = [url] + [url.rstrip("/") + p for p in paths]
enrich = enrich_all(url, urls[:10])

faq_q = enrich.get('faq_quality', {})
print(f'FAQ quality entries: {len(faq_q)}')
for k, v in faq_q.items():
    print(f'  {k[:60]}: {v}')

summary = enrich.get('summary', {})
print(f'\nSummary: pages_with_faq={summary.get("pages_with_faq")}, has_faq_pct={summary.get("has_faq_pct")}')
print(f'Total pages: {summary.get("total_pages")}')

# Check per-page faq status
for normed, data in enrich.get('pages', {}).items():
    faq = data.get('faq', {})
    if faq.get('has_faq'):
        print(f'FAQ found on: {normed[:60]}')
