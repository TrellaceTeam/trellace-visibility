---
type: framework
layer: 4
topic: ai-visibility-audit
status: v1
created: 2026-05-20
---

# Layer 4 — AI Visibility Audit Specification

## What This Is

A repeatable specification for measuring whether a brand actually appears in AI-generated answers. While Layers 1-3 audit readiness, Layer 4 audits reality — through direct polling of AI platforms.

**Executed by:** LLM API calls to ChatGPT, Perplexity, Gemini, Claude (when API keys available) + GA4 (referral traffic) + GSC (branded search volume).
**Input:** Brand name, competitor list, ICP description, prompt list.
**Output:** Mention rate, citation rate, Share of Model, platform breakdown, competitive comparison.

---

## Core Principle

Layer 4 answers the question: **"After all the work in Layers 1-3, are we actually visible?"** It is the outcome layer. Unlike Layers 1-3 which measure inputs (technical quality, content quality, external presence), Layer 4 measures the output: do AI systems cite this brand?

---

## What to Measure

### Metric 1: Brand Mention Rate

**Definition:** % of target prompts where the brand name appears in the AI's response.

**Method:** Run a list of 10-15 prompts across each AI platform. For each response, check if the brand name appears. `mention_rate = mentions / total_prompts`

**Target prompts should include:**
- 5 category prompts: "what's the best [category] software?" (no brand name mentioned)
- 5 problem prompts: "how do I [solve problem the ICP has]?"
- 5 comparison prompts: "[brand] vs [competitor]" or "[competitor] alternatives"

**Benchmark:**
| Mention Rate | Meaning |
|:---:|---------|
| 0% | Invisible |
| 1-15% | Emerging — brand appears occasionally |
| 15-40% | Established — brand is in the consideration set |
| 40%+ | Dominant — brand is a category leader in AI |

**Source:** Top B2B brands achieve 40%+ across platforms per Clearscope/Otterly benchmarks.

---

### Metric 2: Citation Rate

**Definition:** % of target prompts where the AI provides a source link to the brand's content (not just a mention).

**Method:** Same prompt set. Count responses with explicit source links to brand domain.

**Why this differs from mention rate:** AI can mention "Muir AI" without linking. A mention is awareness. A citation is a click pathway. Citations drive referral traffic.

**Benchmark:**
| Citation Rate | Meaning |
|:---:|---------|
| 0% | No click pathway |
| 1-5% | Occasional citations |
| 5-15% | Regular citations |
| 15%+ | Strong citation presence |

---

### Metric 3: Share of Model

**Definition:** Brand's % of total brand mentions in the category, across all prompts, vs competitors.

**Method:** Run category prompts. Count all brands mentioned. `share = brand_mentions / total_brand_mentions`

**Why it matters:** A 31% mention rate means nothing without competitive context. If competitors are at 62%, 31% is bad. If competitors are at 5%, 31% is excellent.

**Benchmark:** Above category average = good. Below = gap.

---

### Metric 4: Citation Position

**Definition:** Where in the AI response does the brand appear? First-mentioned carries strongest implied endorsement.

**Method:** For each mention, record position (1st, 2nd, 3rd, buried).

**Benchmark:**
| Position | Meaning |
|----------|---------|
| 1st | Primary recommendation |
| 2nd-3rd | In the consideration set |
| Buried | Mentioned in passing |

---

### Metric 5: AI Referral Traffic

**Definition:** Actual website visits from AI platforms (chatgpt.com, perplexity.ai, claude.ai, gemini.google.com).

**Method:** GA4 referral report, filtered by AI domains.

**Benchmark:** Track trend month-over-month. Growth = visibility improving. Flat/declining = check Metrics 1-4.

---

### Metric 6: Branded Search Volume

**Definition:** Google searches for the brand name. Leading indicator of AI-driven awareness.

**Method:** GSC: impressions for brand-name queries. Google Trends: search interest over time.

**Why it connects:** AI mentions → people Google the brand → branded searches rise → domain authority increases → more AI mentions (flywheel).

**Benchmark:** Track trend. Rising = flywheel working. Flat = no AI-driven awareness.

---

## Platform-Specific Behavior (Important for Interpretation)

| Platform | Citation Style | Backend | Volatility |
|----------|---------------|---------|------------|
| **ChatGPT** | Inline links when browsing | Bing index + GPTBot | 40-60% month-to-month source churn |
| **Perplexity** | Numbered inline citations | Real-time web search | Most transparent, most volatile |
| **Gemini** | Blended into text | Google index | Moderately stable |
| **Claude** | Contextual mentions | Brave search + training data | Most stable (training data weighted) |
| **Google AI Overviews** | Source cards below | Google index | 97% from top-20 organic |

**Critical note:** API and UI results for the same platform can differ dramatically. The Genezio study (Feb 2026) found zero query overlap between ChatGPT API and ChatGPT.com. API polling gives directional data; UI testing gives what users actually see. For client reports, note this limitation.

---

## Competitive Comparison

Run the same prompt set for each competitor (aPriori, Galorath). Produce:

| Metric | Muir | aPriori | Galorath |
|--------|:---:|:---:|:---:|
| Mention rate | X% | Y% | Z% |
| Citation rate | X% | Y% | Z% |
| Share of Model | X% | Y% | Z% |

This answers: "Are we being out-cited? On which platforms? For which queries?"

---

## Scoring Logic

### Per-Metric Scores (0-10)

| Metric | 0-2 | 3-5 | 6-8 | 9-10 |
|--------|-----|-----|-----|------|
| Mention rate | 0-5% | 5-15% | 15-40% | 40%+ |
| Citation rate | 0% | 1-3% | 3-10% | 10%+ |
| Share of Model | < competitor avg | = competitor avg | > competitor avg | 2× competitor avg |
| Citation position | Never cited | Buried | 2nd-3rd | 1st |
| AI referral traffic | None | < 50/month | 50-200/month | 200+/month |
| Branded search trend | Declining | Flat | Growing slowly | Growing fast |

### Layer Score Calculation

```
layer_score = average of per-metric scores × 10
```

Cap at 100. Minimum 0.

**Audit quality adjustment:** If API keys unavailable (scores based on manual testing or estimates), multiply layer score by 0.7 to reflect lower confidence.

---

## What This Layer Connects To

Layer 4 is the bridge between the visibility framework and the acquisition model:

```
Layer 4 AI mention rate → AI referral traffic → discovery calls → revenue

Layer 4 branded search growth → organic search traffic → discovery calls → revenue

Layer 4 Share of Model → competitive positioning → win rate → revenue
```

---

## Execution Method

1. **Define prompt list:** 10-15 prompts covering category, problem, and comparison queries relevant to ICP.
2. **Poll platforms:** When API keys available, query ChatGPT, Perplexity, Gemini, Claude with each prompt. When keys unavailable, manual testing (weekly, 10-15 prompts). Note: API results differ from UI results.
3. **Count mentions:** For each response, record: brand mentioned? (yes/no), cited? (yes/no), position (1st/2nd/3rd/buried).
4. **Calculate metrics:** Mention rate, citation rate, Share of Model.
5. **Pull GA4:** AI referral traffic from chatgpt.com, perplexity.ai, claude.ai, gemini.google.com.
6. **Pull GSC:** Branded search impressions trend.
7. **Compare competitors:** Run same prompts for aPriori, Galorath.
8. **Output:** Structured JSON with all metrics, competitor comparison, platform breakdown.

---

## Limitations

1. **API ≠ UI.** API results are not what users see. Note this in all reports.
2. **High volatility.** 40-60% month-to-month source churn means single measurements are unreliable. Track trends over multiple weeks.
3. **API key dependency.** Without ChatGPT/Perplexity/Gemini/Claude API keys, manual testing is the fallback. Manual testing has small sample sizes and high variance.
4. **Lag time.** Improvements in Layers 1-3 take 6-8 weeks to show in Layer 4 metrics.
5. **Context dependence.** AI responses vary by user location, session history, and time of day. Blank-canvas testing is reproducible but not realistic.

---

## Repeatability

Same prompts → same platforms → comparable metrics over time. Volatility is high, so single measurements are less meaningful than trends. Run weekly for signal; review monthly for decisions.
