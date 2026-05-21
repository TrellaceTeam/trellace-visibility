---
type: framework
name: trellace-visibility-framework
version: 2.0
created: 2026-05-14
updated: 2026-05-20
status: complete
---

# Trellace Visibility Framework v2

## What This Is

The Trellace Visibility Framework is a complete system for auditing a B2B SaaS company's digital visibility across four layers: Technical Foundation, Content Citability, External Presence, and AI Visibility. It connects each finding to what it improves and ultimately to discovery calls and revenue.

This framework is the product. The tool (auditstack) is the engine. The acquisition model is the business translation layer.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  VISIBILITY FRAMEWORK                        │
│                                                              │
│  L1: Technical  │  L2: Content   │  L3: External  │  L4: AI │
│    Foundation   │   Citability   │   Presence     │Visibility│
│                                                              │
│  ──────────────── Cross-Layer Features ────────────────      │
│  Competitive Comparison │ Priority Ranking │ Remediation     │
│  Anomaly Detection     │ Business Connection (Acq Model)     │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────────┐
│  AUDIT ENGINE    │          │  ACQUISITION MODEL   │
│  (auditstack)    │          │  (channels → KPIs →  │
│  runs the checks │          │   discovery calls)   │
└─────────────────┘          └─────────────────────┘
```

## The Four Layers

### Layer 1: Technical Foundation
**Can the site be found, crawled, and rendered well?**

Binary gates (11 checks) + scalar metrics (Core Web Vitals, schema, indexation, speed, images, caching). 100% deterministic — no LLM needed. Runs via crawl + Lighthouse + GSC. Every benchmark traces to a standards body (Google, Schema.org, IETF, W3C).

**Spec:** [[layer1-spec.md]]

### Layer 2: Content Citability
**Is the content AI-citable, authoritative, and covering the right topics?**

Chunk-level scoring (134-167 word chunks, 15-20% overlap). 85% deterministic (fact density via regex+NER, self-containment via pattern match, readability via Flesch, structure via HTML parse). 15% LLM with rubric (E-E-A-T 20-item rubric with veto system, citation worthiness with anchored 0-10 scale, remediation drafts). Content coverage check against ICP topics and competitors.

**Spec:** [[layer2-spec.md]]
**Rubrics:** [[llm-rubrics.md]]

### Layer 3: External Presence
**Do review sites, social platforms, and publications validate the brand?**

Eight platforms: LinkedIn, G2, Capterra, YouTube, Reddit, Podcasts, Industry Publications, Wikipedia/Wikidata. Each scored on existence, volume, content quality, and ICP alignment. 64% deterministic (direct scraping + APIs). 36% LLM with rubrics (ICP alignment, Reddit sentiment, podcast discovery, publication discovery).

**Spec:** [[layer3-spec.md]]
**Rubrics:** [[llm-rubrics.md]]

### Layer 4: AI Visibility
**When AI is asked about this category, does the brand appear?**

Six metrics: brand mention rate, citation rate, Share of Model, citation position, AI referral traffic, branded search volume trend. All 100% objective (counts, not judgments). Requires API keys for ChatGPT, Perplexity, Gemini, Claude polling. Falls back to manual testing when keys unavailable. 40-60% month-to-month volatility is normal — track trends, not single measurements.

**Spec:** [[layer4-spec.md]]

## Cross-Layer Features

### Competitive Comparison
Every layer runs against the brand AND its competitors. Side-by-side scores, per-layer gap analysis, top-finding comparison. Answers: "Where are they beating us and by how much?"

### Priority Ranking
Every finding is ranked by: `priority = (lift × certainty) / effort`. Severity maps to lift (high=5, medium=3, low=1). Certainty maps to confidence (confirmed=5, likely=3, hypothesis=1). Effort is per-rule (broken_link=1, content_quality=2, low_sov=4, etc.). Finding IDs are deterministic (hash of stage+URL+rule) so the same finding carries forward across audit runs. Highest priority items are what the client should fix first.

### Remediation Drafts
For Layer 2 findings scoring below threshold, the LLM generates 30-80 word copy fixes. Validated for length, tone (educational, not promotional), ICP language, and factual verifiability. Requires Anthropic API for quality tier.

### Anomaly Detection
Compares current audit to previous run for the same site. Detects: layer score drops (≥10 points flagged as sharp anomaly), new findings, resolved findings. First run is a baseline — anomalies appear from the second run onward.

### Business Connection
Every layer connects to the [[../acquisition-model/README.md|acquisition model]]:

| Layer | Feeds These KPIs |
|-------|-----------------|
| L1 (Technical) | Google organic traffic, Google Ads CPC (QS), AI crawlability |
| L2 (Content) | AI citation rate, Google organic traffic, conversion rate, backlinks |
| L3 (External) | AI citation rate, branded search volume, outbound reply rate, LinkedIn acceptance rate |
| L4 (AI Visibility) | AI referral traffic, branded search volume, discovery calls from AI |

These KPIs feed directly into the acquisition model's channels and ultimately to discovery calls.

## The A/B/C Structure

Every layer uses the same quality framework:

| Category | What It Means | In the Report |
|----------|--------------|---------------|
| **A — Binary** | Done or not done. A gate. Either the thing exists or it doesn't. | Pass/Fail indicator per check |
| **B — Scalar** | Done, but can be better or worse. Measured on a spectrum. | Scored against published benchmarks (Good/OK/Bad bands) |
| **C — Uncontrollable** | Things that affect visibility but can't be directly controlled. | Monitored as outcome indicators |

## Scoring Philosophy

A standalone number is meaningless. "Content: 67/100" says nothing. Every score must include:

1. **What it means** — "67 means average citability of 6.7/10. Your solution pages score better (7.2) than your blog posts (5.8)."
2. **What it improves** — "At 67, approximately 60% of your content is citation-ready. Improving to 80+ would likely increase your AI-driven discovery calls."
3. **What to fix** — "The should-cost modeling page scores 7/10 and is close to citable. The cookie policy page drags your average down — it's un-citable but low-importance."
4. **How it compares** — "aPriori's content layer scores 72. Their advantage: better fact density across all pages."

This applies to every score in the framework. Never a number without context.

## The LLM Contract

Where the framework uses LLMs, every call is governed by a rubric:

1. **Anchored scales** — "7/10" means something specific. The rubric defines what 0, 5, and 10 look like with examples.
2. **Required evidence** — The LLM must state what it observed, not just what it scored.
3. **Structured output** — Always JSON. Always the defined schema.
4. **Confidence awareness** — When evidence is thin, lower confidence. "No content to evaluate" = confidence 0.
5. **Outcome calibration** — Periodically compare LLM judgments to actual Layer 4 citation results. Adjust rubrics.

All rubrics are in [[llm-rubrics.md]].

## Related Documents

| Document | Purpose |
|----------|---------|
| [[layer1-spec.md]] | Technical Foundation audit specification |
| [[layer2-spec.md]] | Content Citability audit specification |
| [[layer3-spec.md]] | External Presence audit specification |
| [[layer4-spec.md]] | AI Visibility audit specification |
| [[llm-rubrics.md]] | Rubrics for every LLM call in the framework |
| [[discovery-model.md]] | Topic-to-discovery-call connection map |
| [[../acquisition-model/README.md]] | Acquisition model: channels → KPIs → discovery calls |

## Sources

- Core Web Vitals thresholds: Google Web Vitals
- Schema.org standards: W3C / Schema.org
- llms.txt spec: llmstxt.org
- LinkedIn benchmarks: Databox (440 B2B orgs, 2026), Socialinsider (2026), ThoughtCred (2026)
- G2 benchmarks: G2 Grid Reports, G2 Year in Review 2025
- YouTube-AI correlation: Ahrefs 75K brand study (Dec 2025)
- Reddit citation rates: Multiple 2026 studies
- Podcast benchmarks: Command Your Brand (2026), EvolveAMZ (2026)
- E-E-A-T framework: Google Search Quality Rater Guidelines
- CORE-EEAT framework: seo-geo-claude-skills (aaron-he-zhu)
- Deterministic content scoring: llm-citeops (rakeshcheekatimala)
- RAG chunk retrieval research: KDD 2024 GEO study, CPS framework
- API vs UI divergence: Genezio study (Feb 2026)
