---
type: framework
layer: 1
topic: technical-foundation-audit
status: v1
created: 2026-05-20
---

# Layer 1 — Technical Foundation Audit Specification

## What This Is

A repeatable specification for auditing a website's technical foundation: speed, structure, schema, crawlability, and AI access. This is Layer 1 of the visibility framework.

**Executed by:** auditstack (crawl + Lighthouse + schema) + lightweight custom checks (AI crawlers, llms.txt).
**Input:** URL.
**Output:** Per-check scores, binary pass/fail, layer score, prioritized findings.

---

## Core Principle

Layer 1 is the most objective layer. Everything is measurable by machines. There are no LLM judgments here — only deterministic checks against well-established standards. Every benchmark has a published source from the organization that defines the standard (Google, W3C, Schema.org, IETF).

---

## Check Categories

### A — Binary Checks (Pass/Fail)

These are gates. Fail = immediate action needed. No partial credit.

| ID | Check | How to Verify | Source of Truth | Why It Matters |
|----|-------|---------------|-----------------|----------------|
| T1.1 | HTTPS valid | Browser + Lighthouse | IETF TLS standard | Security baseline. Google ranking factor since 2014. |
| T1.2 | XML sitemap present | Crawl + manual check | Google | Required for indexation. Without it, Google discovers pages slowly. |
| T1.3 | Sitemap submitted to GSC | GSC API | Google | Tells Google which pages to prioritize. |
| T1.4 | No broken links (internal 404s) | auditstack crawl | HTTP standard | Broken links = wasted crawl budget + bad UX. |
| T1.5 | No redirect chains | auditstack crawl | HTTP standard | Each redirect adds latency. Google stops following after 5 hops. |
| T1.6 | Canonical URLs correct on all pages | auditstack crawl | Google | Prevents duplicate content penalties. |
| T1.7 | Mobile responsive | Lighthouse mobile audit | Google | Mobile-first indexing since 2019. Non-responsive = ranking penalty. |
| T1.8 | Breadcrumb navigation present | auditstack crawl | Google | Helps Google understand site hierarchy. Enables breadcrumb rich results. |
| T1.9 | Custom 404 page exists | auditstack crawl | Google | Dead pages should return 404, not soft-404 or redirect to homepage. |
| T1.10 | AI crawlers not blocked in robots.txt | Manual check: GPTBot, ClaudeBot, PerplexityBot, Google-Extended | Each AI platform's documentation | If blocked, content invisible to AI regardless of quality. |
| T1.11 | llms.txt file exists at domain root | Manual check: GET /llms.txt | llmstxt.org spec | AI-native sitemap. Guides LLMs to priority content. |
| T1.12 | Organization schema present (site-wide) | auditstack schema check | Schema.org | Entity recognition for Knowledge Graph + AI. |

---

### B — Scalar Checks (Measured on a Spectrum)

Each has specific thresholds with published sources.

#### Core Web Vitals

| ID | What | Measurement | Good | Needs Work | Bad | Source |
|----|------|------------|------|------------|-----|--------|
| T1.LCP | Largest Contentful Paint | Lighthouse / CrUX field data (75th percentile) | < 2,500ms | 2,500–4,000ms | > 4,000ms | Google Web Vitals |
| T1.INP | Interaction to Next Paint | CrUX field data (75th percentile) | < 200ms | 200–500ms | > 500ms | Google Web Vitals |
| T1.CLS | Cumulative Layout Shift | Lighthouse / CrUX | < 0.1 | 0.1–0.25 | > 0.25 | Google Web Vitals |
| T1.TTFB | Time to First Byte | Lighthouse / WebPageTest | < 200ms | 200–600ms | > 600ms | Google |

**Why these numbers:** These are Google's published thresholds. Pages below the "good" threshold get ranking benefits. Pages in "poor" get demoted. LCP > 4s and CLS > 0.25 are confirmed negative ranking signals. INP > 300ms correlates with ~31% ranking drops on mobile.

**Note:** LCP, INP, and CLS are measured from real-user data (Chrome User Experience Report) when available. Lighthouse provides lab data as a fallback.

#### Schema Completeness

| ID | What | Measurement | Good | OK | Bad | Source |
|----|------|------------|------|----|-----|--------|
| T1.SCHEMA | Schema types implemented vs recommended | Count types found / count types recommended for this content | All 6+ types present, zero errors | 4-5 types, no errors | < 4 types or errors present | Schema.org |

**Recommended types:** Organization (always), Article (blog posts), FAQPage (Q&A content), HowTo (tutorials), SoftwareApplication (product pages), BreadcrumbList (always), LocalBusiness (if applicable).

**Error handling:** One error blocks rich results for the entire page. Zero errors is not optional — it's the minimum.

#### Indexation

| ID | What | Measurement | Good | OK | Bad | Source |
|----|------|------------|------|----|-----|--------|
| T1.INDEX | Indexed page ratio | Indexed pages / total crawled pages (via GSC) | > 90% indexed | 70–90% | < 70% | Google Search Console |
| T1.CRAWL | Crawl budget efficiency | Important pages crawled in last week / total crawled | All important pages crawled | Most | Many missed | Google |

Requires GSC OAuth. Without GSC, this check returns "unknown" and the layer score is adjusted down for audit quality.

#### Page Speed

| ID | What | Measurement | Good | OK | Bad | Source |
|----|------|------------|------|----|-----|--------|
| T1.SPEED | Lighthouse Performance score | 0-100 composite | 90+ | 50–89 | < 50 | Google Lighthouse |
| T1.ACCESS | Lighthouse Accessibility score | 0-100 | 90+ | 70–89 | < 70 | Google Lighthouse |
| T1.BP | Lighthouse Best Practices score | 0-100 | 90+ | 70–89 | < 70 | Google Lighthouse |
| T1.SEO | Lighthouse SEO score | 0-100 | 90+ | 70–89 | < 70 | Google Lighthouse |

#### Image Optimization

| ID | What | Measurement | Good | OK | Bad | Source |
|----|------|------------|------|----|-----|--------|
| T1.IMG | Image format optimization | % images in WebP/AVIF format (Lighthouse audit) | > 90% WebP/AVIF | 50–90% | < 50% | Google |
| T1.IMG_SIZE | Image dimensions set | % images with explicit width/height (prevents CLS) | 100% | 80–99% | < 80% | Google CLS guidance |
| T1.IMG_LAZY | Lazy loading | % below-fold images with loading="lazy" | > 90% | 50–90% | < 50% | Google |

#### Caching

| ID | What | Measurement | Good | OK | Bad | Source |
|----|------|------------|------|----|-----|--------|
| T1.CACHE | Cache headers configured | Cache-Control present on static assets | > 90% | 50–90% | < 50% | IETF HTTP caching |

---

## Layer Score Calculation

**Binary checks (40% of score):**
T1.1 - T1.12 each worth 1 point if passed. 
`binary_score = (passed / 12) * 100`

**Scalar checks (60% of score):**
Core Web Vitals (40% of scalar weight), Schema (10%), Indexation (10%), Speed (10%), Images (10%), Caching (10%), Mobile/responsive included in Lighthouse SEO score (10%).
`scalar_score = weighted average of all scalar checks`

**Layer score:**
`layer_score = 0.4 * binary_score + 0.6 * scalar_score`

Capped at 100. Minimum 0.

---

## What This Layer Improves When Done Well

| Check | Directly Improves |
|-------|-------------------|
| Core Web Vitals (LCP, INP, CLS) | Google ranking position, Google Ads Quality Score (Landing Page Experience → lower CPC), user bounce rate, conversion rate |
| Schema markup | Rich snippets (higher CTR from same ranking), AI content parsing, Knowledge Panel eligibility |
| AI crawler access + llms.txt | AI citation rate (prerequisite — without access, content is invisible to AI) |
| Indexation + sitemap | Content discovery by Google, crawl efficiency |
| Broken links | Crawl budget, user experience, site trust |
| SSL + mobile + redirects | Google ranking signals, user trust |
| Images + caching | Page speed, user experience, Core Web Vitals |

---

## Sources of Truth

| Standard | Defined By | Where to Verify |
|----------|-----------|-----------------|
| Core Web Vitals thresholds | Google | PageSpeed Insights, CrUX |
| Schema.org types and validation | W3C / Schema.org | Google Rich Results Test, Schema Markup Validator |
| robots.txt spec | IETF / Google | Manual check |
| llms.txt spec | Answer.AI / llmstxt.org | Manual check |
| TLS/SSL | IETF | Browser |
| HTTP caching | IETF | Response headers |
| Lighthouse scores | Google | Lighthouse CLI |

All benchmarks trace to a standards body or platform owner. None are invented by us.

---

## Execution Method

1. **Crawl:** auditstack crawls up to 500 pages. Collects broken links, redirect chains, schema types, robots.txt, sitemap.
2. **Lighthouse:** auditstack runs Lighthouse on homepage. Collects LCP, CLS, INP, Performance, Accessibility, Best Practices, SEO.
3. **GSC:** If OAuth connected, pull indexed page count, top queries, crawl stats.
4. **Manual supplement:** Check AI crawler access (GPTBot, ClaudeBot, PerplexityBot in robots.txt). Check llms.txt existence and format.
5. **Score:** Compute binary + scalar scores using formulas above.
6. **Output:** Structured JSON with per-check pass/fail + per-metric score + layer score + prioritized findings.

**Automation note:** All checks can be automated except AI crawler access and llms.txt format validation, which currently require a small script to curl and parse robots.txt and llms.txt. These can be added to the audit pipeline with minimal effort.

---

## Repeatability

Same URL → same crawl results → same scores. No LLM subjectivity in this layer. All benchmarks are published standards. This is the most repeatable and defensible layer.
