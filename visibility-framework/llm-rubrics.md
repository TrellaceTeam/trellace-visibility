---
type: framework
topic: llm-rubrics
status: v1
created: 2026-05-20
---

# LLM Rubrics — What Success Looks Like

Every LLM call in the visibility framework must have a rubric. The rubric defines what the LLM is looking for, what evidence counts, and what each score means. Without this, "7/10" is meaningless.

---

## Rubric 1: ICP Alignment

**Used in:** Layer 2 (content coverage vs competitors), Layer 3 (LinkedIn, G2, Capterra, YouTube, Podcasts descriptions)

**What we're asking the LLM:** "Does this content match what the company actually does and who they serve?"

### Input
- The content being evaluated (LinkedIn description, G2 profile text, YouTube video topic, podcast episode topic)
- The ICP description (what the company does, who they serve, key terms)

### Scoring

| Score | Meaning | Criteria |
|:-----:|---------|----------|
| **Aligned** | Content accurately describes the company's current positioning | Key ICP terms appear (e.g., "should-cost modeling," "tariff analysis," "manufacturing cost"). Content describes the right use case for the right audience. |
| **Partially aligned** | Content mentions the company but with outdated, incomplete, or partially wrong positioning | Some ICP terms appear but the primary framing is different (e.g., "carbon footprint platform" when ICP is "cost modeling"). Mentions old product focus. |
| **Misaligned** | Content describes the company in a way that contradicts the ICP | Wrong category entirely. Describes a different product. Positions for a different buyer. |
| **No content** | No content exists to evaluate | Profile doesn't exist, page is blank, or content is boilerplate with no substance. |

### Examples

Aligned: "Muir AI provides should-cost modeling and tariff analysis for manufacturers, helping supply chain teams reduce costs and build resilience."
Partially aligned: "Muir AI is a sustainability platform that helps companies measure their carbon footprint."  
Misaligned: "Muir AI is a CRM for sales teams."
No content: Profile exists but has only a company name and no description.

---

## Rubric 2: E-E-A-T Content Quality

**Used in:** Layer 2 (per-page content quality audit)

**Based on:** CORE-EEAT framework (80 items, 8 dimensions). Simplified to 20 key items for practical LLM execution.

### Input
- Page content (full text)
- Page metadata (title, author, date, schema types)

### Scoring (per item)

| Score | Meaning |
|:-----:|---------|
| **Pass (10)** | The item is clearly and unambiguously present |
| **Partial (5)** | The item is partially present or implied but not explicit |
| **Fail (0)** | The item is absent or the opposite is true |
| **N/A** | The item cannot be evaluated for this content type |

### The 20 Items

**Experience (5 items)**
E1. First-person evidence: Does the content reference specific experiences, cases, or examples the author was directly involved in? (e.g., "we tested 200 suppliers over 18 months")
E2. Original data: Does the content present data the company generated itself? (surveys, benchmarks, tests)
E3. Practical application: Does it show how something was actually done, not just theory? (step-by-step, screenshots)
E4. Limitations stated: Does it acknowledge what the approach doesn't cover or where it falls short?
E5. Audience-specific: Is it written for the actual ICP, using their language, addressing their specific context?

**Expertise (5 items)**
Ep1. Technical accuracy: Are terms used correctly? Are claims technically sound?
Ep2. Depth: Does it go beyond surface-level explanation into meaningful detail?
Ep3. Current knowledge: Does it reference recent developments, current standards, or updated methods?
Ep4. Credentials visible: Is the author's relevant expertise stated? (role, background, qualifications)
Ep5. Appropriate complexity: Is it detailed enough for the ICP without being unnecessarily dense?

**Authority (5 items)**
A1. External sources cited: Does it reference and link to credible external sources?
A2. Industry recognition: Does it mention awards, certifications, partnerships, or industry acknowledgment?
A3. Backlink profile: Is the page linked to from other authoritative sites? (requires external data)
A4. Brand recognition: Is the company/brand established enough to be recognized in its field?
A5. Comparative context: Does it position itself against alternatives or the status quo?

**Trust (5 items)**
T1. Contact accessible: Is there a clear way to reach the company/author?
T2. Editorial transparency: Is it clear who wrote this, when, and whether it's been reviewed?
T3. Factual claims sourced: Are statistics, claims, and data points attributed to a named source?
T4. No deceptive patterns: No hidden affiliate links, no misleading claims, no fake scarcity.
T5. Accuracy signals: Does the content appear factually correct? No obvious errors, outdated claims, or contradictions?

### Dimension Score
```
dimension_score = (sum of 5 items) / (5 * 10) * 100
```

### Overall E-E-A-T Score
```
eeat_score = average of 4 dimension scores
```

### Veto System
- **One veto fail (T3, T4, or A1):** Content is marked UNRELIABLE. Overall score capped at 50.
- **Two or more veto fails:** Content is marked BLOCKED. Do not publish without major revision.

### Content Type Weights
| Content Type | Experience | Expertise | Authority | Trust |
|-------------|:---:|:---:|:---:|:---:|
| Blog post (educational) | 25% | 30% | 15% | 30% |
| Product/solution page | 20% | 20% | 25% | 35% |
| Case study | 40% | 25% | 15% | 20% |
| About/company page | 30% | 15% | 25% | 30% |
| FAQ page | 15% | 35% | 15% | 35% |

---

## Rubric 3: Reddit Sentiment & Quality

**Used in:** Layer 3 (Reddit presence audit)

### Input
- Reddit post/comment text mentioning the brand
- Subreddit context
- Post metadata (upvotes, replies)

### Sentiment Scoring

| Score | Meaning | Criteria |
|:-----:|---------|----------|
| **Positive** | The mention is favorable | Recommends the product. Shares a positive experience. Defends the brand. |
| **Neutral** | The mention is factual or undirected | Names the brand in a list. Mentions it without opinion. Asks a question about it. |
| **Negative** | The mention is unfavorable | Complains about the product. Recommends against it. Criticizes the company. |

### Content Quality Scoring

| Score | Meaning | Criteria |
|:-----:|---------|----------|
| **Genuine** | Appears to be authentic user sentiment | Specific details, personal experience, nuanced opinion, natural language, upvotes from community. |
| **Suspicious** | Unclear if authentic | Generic praise without specifics. New account. No community history. |
| **Promotional** | Appears to be marketing | Marketing language, calls to action, brand talking points, posted by company-associated account. |

### What Makes a Mention Valuable
High-value: positive + genuine + specific details + in a relevant subreddit + decent upvotes.
Low-value: neutral + suspicious + generic + in an irrelevant subreddit + no engagement.
Negative value: promotional content that gets called out by the community.

---

## Rubric 4: Podcast Discovery

**Used in:** Layer 3 (podcast presence audit)

### What We're Asking the LLM
"Search for evidence that this brand or its representatives have appeared as podcast guests. Identify the podcast name, episode topic, whether a transcript is available, and whether the topic is relevant to the ICP."

### Success Criteria

| Finding | Meaning |
|---------|---------|
| **Confirmed appearance** | Podcast episode found with brand representative as named guest. Show name, episode title, and date are verifiable. |
| **Likely appearance** | Evidence suggests an appearance (social media post, mention in show notes) but the episode itself couldn't be verified. |
| **Brand mentioned in episode** | Brand discussed but no representative appeared as guest. |
| **No evidence** | No podcast presence found. |

### Transcript Value

| Finding | AI Value |
|---------|----------|
| **Transcript published on company site** | Maximum — indexed by search engines, full content retrievable |
| **Transcript on podcast host site** | High — indexed, retrievable, linked to show |
| **Auto-generated captions (YouTube version)** | Medium — indexed but less accurate |
| **No transcript** | Low — audio-only, not retrievable by AI |

### Topic Relevance

| Score | Criteria |
|:-----:|----------|
| **Directly relevant** | Episode topic matches ICP industry and problems (e.g., "How AI is transforming manufacturing cost estimation") |
| **Adjacent** | Related to ICP space but not directly (e.g., "Supply chain sustainability trends") |
| **General business** | About startups, leadership, fundraising — not ICP-specific |
| **Irrelevant** | Topic has no connection to ICP |

---

## Rubric 5: Remediation Drafts

**Used in:** Layer 2 (generating copy fixes for low-scoring content)

### What We're Asking the LLM
"Generate a 30-80 word replacement for this content chunk that fixes [specific problem] while preserving the original topic and factual content."

### Problem Types and Fix Strategy

| Problem | Fix Strategy | Example |
|---------|-------------|---------|
| Answer buried | Move declarative answer to first sentence. Remove preamble. | Before: "In today's competitive manufacturing landscape, companies are increasingly looking for ways to reduce costs. Muir AI provides..." / After: "Muir AI provides should-cost modeling that helps manufacturers reduce product costs by analyzing supplier data, material prices, and tariff impacts in real time." |
| Too short (under 100 words) | Expand with specific details, numbers, or examples | Add: "The platform processes over 10,000 supplier quotes daily, identifying cost reduction opportunities averaging 12-15% per product line." |
| Not self-contained | Rewrite to remove external references. Make standalone. | Remove: "As mentioned in the previous section..." / Replace with: Include the referenced information directly. |
| Low fact density | Add data points, statistics, or named sources | Add: "According to McKinsey's 2025 Manufacturing Report, companies using AI-driven cost modeling reduce supplier costs by an average of 18% within the first year." |
| Promotional language | Rewrite in educational, third-person tone | Remove: "Our revolutionary, industry-leading platform..." / Replace with: "AI-powered cost modeling platforms analyze..." |
| Missing freshness signal | Add date anchor | Add: "As of Q2 2026, manufacturers face an average tariff increase of 7.2% across 14 affected categories, according to USITC data." |
| No author signals | Add implied expertise | Add: "Drawing on analysis of 50,000+ supplier relationships across 12 manufacturing sectors..." |

### Validation Checklist
Before accepting a remediation draft, verify:
1. Length: 30-80 words
2. Content: Does it preserve the original meaning?
3. Facts: Are any added facts verifiable? (If not, mark as "needs verification")
4. Tone: Educational, not promotional
5. ICP: Uses terminology the target audience would recognize

---

## Rubric 6: Citation Worthiness (The Only Remaining LLM Judgment)

**Used in:** Layer 2 (per-chunk scoring)

This is the one LLM-scored dimension we can't fully replace with deterministic checks. But we can constrain it.

### What We're Asking
"Rate how likely an AI system would be to retrieve and cite this chunk if asked about the page's topic. Score 0-10."

### Anchoring Criteria

| Score | Meaning | Signal |
|:-----:|---------|--------|
| **9-10** | Almost certainly citable | Chunk directly answers a clear question. Contains unique, specific information not available elsewhere. Well-structured, self-contained, fact-dense. |
| **7-8** | Likely citable | Strong content that covers the topic well. Good structure and facts. Minor issues (slightly too long, one missing source). |
| **5-6** | Possibly citable | Decent content but generic — similar content exists elsewhere. Lacks standout facts. OK structure. |
| **3-4** | Unlikely citable | Thin, generic, or poorly structured. Better sources almost certainly exist for this topic. |
| **1-2** | Very unlikely citable | Vague, promotional, or irrelevant to any likely query. |
| **0** | Not citable | Cookie policy, navigation, boilerplate, or completely off-topic. |

### What Counts as Evidence
The LLM must reference specific signals in its reasoning, not just state the score:
- "This chunk opens with a clear declarative answer and contains 3 specific statistics, making it highly citable" (score 8-9)
- "This chunk is generic marketing copy with no specific data and could describe any competitor" (score 2-3)
- "This chunk is navigation boilerplate with no substantive content" (score 0)

---

## Rubric Execution Rules

1. **Always provide the rubric in the prompt.** Never ask an LLM to "rate 0-10" without criteria.
2. **Always require evidence.** The LLM must state what it saw, not just the score.
3. **Calibrate against outcomes.** Periodically compare LLM scores to actual Layer 4 citation results. Adjust rubrics.
4. **Use structured JSON output.** Every rubric returns a defined schema, not free text.
5. **Confidence scoring.** When evidence is thin, the LLM should lower confidence. "No content to evaluate" → confidence = 0.

---

## Rubric 7: Industry Publication Discovery

**Used in:** Layer 3 (industry publications presence audit)

### What We're Asking the LLM
"Search for evidence that this brand has been covered in, contributed to, or mentioned by industry publications, news outlets, or trade press. Identify the publication, article topic, type (earned vs contributed), and estimated authority."

### Success Criteria

| Finding | Meaning |
|---------|---------|
| **Confirmed earned coverage** | Independent article about the brand. Publication name, article title, date verifiable. |
| **Confirmed contributed article** | Brand executive's byline on third-party industry site. |
| **Brand mentioned in article** | Referenced in passing within a broader industry piece. |
| **Company blog only** | Content only on brand's own domain. Does NOT count. |
| **No evidence** | No publication presence found. |

### Publication Authority

| Tier | Criteria | Multiplier |
|------|----------|:---:|
| Tier 1 | Major press (TechCrunch, Forbes, WSJ). DR 70+. | ×1.5 |
| Tier 2 | Industry publications (Supply Chain Dive, Manufacturing.net). DR 40-69. | ×1.0 |
| Tier 3 | Niche blogs, Medium, low-authority. DR < 40. | ×0.5 |
| Tier 4 | Own domain, press releases, paid placements. | ×0.0 |

### What Counts vs Doesn't

| Counts | Doesn't Count |
|--------|--------------|
| Independent journalist article | Press release on wire services |
| Executive byline on industry site | Blog post on own domain |
| Mention in industry trend piece | Paid/sponsored content |
| Research citing company data | Job listing on database site |
