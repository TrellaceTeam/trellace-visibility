import httpx, xml.etree.ElementTree as ET
url = 'https://www.muir.ai'
urls = [url]
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
except Exception as e:
    print(f'Sitemap: {e}')
for path in ["/solutions-should-cost-modeling","/solutions-pcf-reporting",
             "/solutions-tariff-analysis","/industries-electronics",
             "/blog","/stories","/build-a-product-model","/about"]:
    u = url.rstrip("/") + path
    if u not in urls:
        urls.append(u)
print(f'URLs: {len(urls)}')
for u in urls:
    print(f'  {u[-60:]}')
