import httpx
paths = ['/solutions-should-cost-modeling', '/solutions-pcf-reporting', '/solutions-tariff-analysis']
for p in paths:
    u = 'https://www.muir.ai' + p
    try:
        with httpx.Client(timeout=5, follow_redirects=True) as c:
            r = c.head(u)
        print(f'{p}: {r.status_code}')
    except Exception as e:
        print(f'{p}: {e}')
