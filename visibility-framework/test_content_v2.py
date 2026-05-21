"""Quick test - debug Parallel.ai extract response structure"""
import importlib.util, sys, json
spec = importlib.util.spec_from_file_location('cs', 'context/knowledge/visibility-framework/content_stage_v2.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['cs'] = mod
spec.loader.exec_module(mod)

urls = [
    'https://www.muir.ai',
    'https://www.muir.ai/solutions-should-cost-modeling',
    'https://www.muir.ai/solutions-pcf-reporting',
]
print(f'Batch extracting {len(urls)} pages...')
extract = mod.parallel_extract(urls, 'full content for citability')

results = extract.get('results', [])
print(f'Results: {len(results) if isinstance(results, list) else type(results)}')
for i, item in enumerate(results):
    u = item.get('url','')
    fc = item.get('full_content','')
    print(f'  [{i}] url={u[:80]} content_len={len(fc)}')
