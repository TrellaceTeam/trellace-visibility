# Trellace Visibility Audit

Open-source visibility audit engine for B2B SaaS. One command, four layers, a working report.

## Quick Start

```bash
pip install auditstack httpx textstat
python3 run_audit.py https://your-site.com
```

## What It Audits

| Layer | What It Checks |
|-------|---------------|
| **L1: Technical** | Core Web Vitals, schema, broken links, AI crawlers, llms.txt, caching |
| **L2: Content** | Chunk citability, E-E-A-T, readability, FAQ quality, fact density |
| **L3: External** | G2, Capterra, LinkedIn, YouTube, Reddit, podcasts, publications, Wikipedia |
| **L4: AI Visibility** | Multi-model SOV polling (ChatGPT, Claude, Perplexity-ready, Gemini-ready) |

## Output

`audits/{id}/v1/trellace-report.html` — standalone, client-ready report with:
- Per-layer A/B/C structure (binary gates + scalar metrics + uncontrollable)
- Priority-ranked actions with [how?] fix dropdowns
- Per-page scoring for content citability
- LLM-generated remediation drafts
- Multi-model AI visibility results

## Configuration

Set API keys as environment variables or in `.env`:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."
export DEEPSEEK_KEY="sk-..."      # for content scoring (cheap tier)
```

Optional:
```bash
export PERPLEXITY_API_KEY="..."   # for AI polling
export GOOGLE_API_KEY="..."       # for Gemini polling
```

## Options

```bash
python3 run_audit.py https://site.com \
    --name "Company Name" \
    --description "What they do" \
    --competitors "competitor1.com,competitor2.com" \
    --pages 8 \
    --no-l4                         # skip AI polling for speed
```

## License

MIT
