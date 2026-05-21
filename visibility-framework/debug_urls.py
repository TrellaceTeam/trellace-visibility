"""Quick debug: URL matching issue."""
import json, urllib.request

PARALLEL_KEY = "KtepRKsixtAmtjSnaUP-U3wxmqLKiM3gkC_Q9YAW"
urls = [
    "https://www.muir.ai",
    "https://www.muir.ai/solutions-should-cost-modeling",
    "https://www.muir.ai/solutions-pcf-reporting",
]

req = urllib.request.Request(
    "https://api.parallel.ai/v1beta/extract",
    data=json.dumps({"urls": urls, "objective": "test", "full_content": True}).encode(),
    headers={"x-api-key": PARALLEL_KEY, "Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())

def _norm(u):
    return u.replace('https://','').replace('http://','').replace('www.','').rstrip('/')

print(f"Input URLs: {[_norm(u) for u in urls]}")
print(f"\nParallel.ai returned {len(data['results'])} results:")
for item in data["results"]:
    item_url = item.get("url", "")
    content_len = len(item.get("full_content", ""))
    matched = "?"
    for u in urls:
        if _norm(u) == _norm(item_url):
            matched = _norm(u)
    print(f"  url: {item_url} → content: {content_len} chars → matched: {matched}")
