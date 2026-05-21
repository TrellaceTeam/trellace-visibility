---
type: framework
layer: 3
topic: external-presence-audit
status: v1
created: 2026-05-20
---

# Layer 3 — External Presence Audit Specification

## What This Is

A repeatable specification for auditing a B2B SaaS company's external presence across review platforms, social platforms, media, and knowledge bases. This is Layer 3 of the visibility framework.

**Executed by:** An LLM + search API (Parallel.ai Search/Extract or equivalent web scraping).
**Input:** Brand name + ICP description (what the company does, who it serves, keywords).
**Output:** Per-platform scores with evidence, content alignment check, improvement mapping, and recommendations.

---

## Core Principle

We are not checking existence. We are checking existence + volume + content quality + ICP alignment. A profile that exists but says the wrong things is worse than no profile — it misleads both buyers and AI.

---

## Scoring Dimensions Per Platform

Every platform is scored on these four dimensions, then combined into a 0-10 score:

| Dimension | What It Means | Source of Truth |
|-----------|---------------|----------------|
| **Existence** | Does the profile/page exist at all? Binary gate. | Search results |
| **Volume** | How much content is there? Reviews, posts, videos, mentions. | Search results + benchmarks |
| **Content Quality** | Is the content well-crafted? Descriptions, transcripts, post substance. | Extracted content |
| **ICP Alignment** | Does the content say what it should say? Right keywords, right positioning, right category. | Extracted content vs ICP description |

**Existence is a gate.** If existence = 0, volume, quality, and alignment are all 0.

**ICP alignment is the multiplier.** Well-written content about the wrong thing (e.g., "carbon management" when the ICP is "cost modeling") is misaligned. Score it lower.

---

## Platform Specifications

### LinkedIn

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Company page exists | Search results + Linkedin URL extraction | Must exist | — |
| Follower count | Search or extract | Median B2B: 4,500. Good: 5K-25K. Excellent: 25K+ | Databox, 440 B2B orgs, 2026 |
| Description content | Extract company page | Must include: what company does, who it serves, ICP-relevant keywords | — |
| Posting frequency | Search for recent posts | Good: 2-3 posts/week | Socialinsider 2026 |
| Post content quality | Extract recent posts | Carousels/PDFs > multi-image > text. Educational > promotional. | Socialinsider 2026 |
| Employee profiles active | Search for CEO + key team | Personal profiles drive 561% more reach than company page | van der Blom 2026 |
| ICP alignment | Compare description + posts to ICP | Keywords must match ICP. Category terms should appear. | — |

**Scoring logic (0-10):**
- Start at 0. Add points for each verified signal. Cap at 10.
- Existence: +0 if no page, +2 if page exists
- Followers: +0 if < 1K, +1 if 1K-5K, +2 if 5K-25K, +3 if 25K+
- Description quality: +0 if missing, +1 if present, +2 if well-written with ICP keywords
- Posting: +0 if never, +1 if occasional, +2 if 2-3/week
- ICP alignment: ×1.0 if aligned, ×0.5 if partially, ×0.0 if misaligned (multiplier on total)

**What this improves when done well:**
- AI visibility (LinkedIn content indexed by search engines)
- Branded search volume (profile views → Google searches)
- Outbound acceptance rate (prospect recognizes name from LinkedIn)
- Retargeting pool size (LinkedIn engagement → matchable audience)

---

### G2

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Profile exists | Search results | Must exist — 100% of ChatGPT-cited tools have G2 | Ahrefs 75K brands |
| Review count | Search or extract | 10 = Grid minimum. 50 = competitive. 100+ = strong | G2 Grid Reports |
| Average rating | Search or extract | 4.5+ = buyer trust threshold | Industry |
| Profile completeness | Search or extract | Screenshots, demo video, pricing, AI-focused keywords | — |
| Category alignment | Search or extract | Category must match ICP. Wrong category misleads buyers + AI. | — |
| Review recency | Search or extract | Reviews from last 90 days weighted highest | G2 |
| ICP alignment | Compare profile text to ICP | Description must use ICP keywords. Old positioning = misaligned. | — |

**Scoring logic (0-10):**
- Existence: +0 if no profile, +2 if profile exists
- Reviews: +0 if < 10, +1 if 10-49, +2 if 50-99, +3 if 100+
- Rating: +0 if < 4.0 or none, +1 if 4.0-4.4, +2 if 4.5+
- Completeness: +1 if profile has screenshots/demo/video
- Category alignment: ×1.0 if correct, ×0.5 if partially, ×0.0 if wrong category

**What this improves when done well:**
- AI citation rate (inclusion gate — AI scrapes G2 for verification)
- Buyer trust (social proof → higher demo conversion)
- Outbound reply rate (prospect checks G2 before replying)
- Direct discovery (buyers browse G2 categories)

---

### Capterra

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Profile exists | Search results | Must exist — 99% of ChatGPT-cited tools have Capterra | Ahrefs 75K brands |
| Review count | Search or extract | 50+ = competitive | Capterra |
| Average rating | Search or extract | 4.5+ = good | Industry |
| Category alignment | Search or extract | Category must match ICP | — |
| ICP alignment | Compare profile text to ICP | Description must use ICP keywords | — |

**Scoring logic (0-10):**
Same structure as G2 but fewer signals (Capterra has less rich profile data):
- Existence: +0 or +2
- Reviews: +0 if < 10, +1 if 10-49, +2 if 50+
- Rating: +0 if < 4.0, +1 if 4.0+, +2 if 4.5+
- Category alignment: ×1.0 / ×0.5 / ×0.0

**What this improves:** Same as G2.

---

### YouTube

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Channel exists | Search results | Must exist | — |
| Video count | Search or extract | 10+ videos = good | — |
| Transcript quality | Search for transcripts | Human-reviewed > auto-captions | Ahrefs 75K brands |
| Title format | Search or extract | Question-format titles perform better | Industry |
| Description quality | Search or extract | 3-5 paragraph descriptions with timestamps | Industry |
| ICP alignment | Compare video topics to ICP | Content should address ICP problems | — |
| Third-party mentions | Search for brand in non-owned videos | YouTube mentions = strongest AI signal (0.737) | Ahrefs Dec 2025 |

**Scoring logic (0-10):**
- Existence: +0 if no channel and no third-party mentions, +1 if third-party only, +2 if own channel exists
- Videos: +0 if < 3, +1 if 3-9, +2 if 10+
- Transcripts: +1 if auto-captions, +2 if human-reviewed
- Descriptions: +1 if present, +2 if rich (3-5 paragraphs with timestamps)
- Third-party mentions: +1 if any, +2 if multiple
- ICP alignment: ×1.0 / ×0.5 / ×0.0

**What this improves when done well:**
- AI citation rate (strongest single signal: 0.737 correlation)
- Google AI Overviews presence (29.5% cite YouTube)
- Organic search (YouTube results appear in Google)
- Branded search (YouTube → Google search pipeline)

---

### Reddit

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Brand mentioned at all | Search | Must have some presence | — |
| Mention count | Search | Multiple mentions across threads | — |
| Community relevance | Search | 3-5 relevant subreddits | Based on ICP industries |
| Content quality | Search + extract | Genuinely helpful, not promotional. AI detects promo language. | — |
| Sentiment | Search | Positive/neutral > negative | — |
| ICP alignment | Compare discussion topics to ICP | Are people talking about the right problems? | — |

**Scoring logic (0-10):**
- Existence: +0 if none, +2 if any mentions
- Volume: +0 if < 3 mentions, +1 if 3-10, +2 if 10+
- Communities: +1 if 1-2, +2 if 3-5 relevant subreddits
- Quality: +0 if promotional or spam, +1 if mixed, +2 if genuinely helpful
- Sentiment: ×1.0 if positive/neutral, ×0.5 if mixed, ×0.0 if negative
- ICP alignment: ×1.0 / ×0.5 / ×0.0

**What this improves when done well:**
- AI citation rate (46.7% of Perplexity citations, 11.3% of ChatGPT)
- Corroboration threshold (AI treats Reddit as real user sentiment)
- Branded search (Reddit threads rank in Google)
- Direct referral traffic

---

### Podcasts

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Any appearances | Search | Must have some | — |
| Appearance count | Search | 2-4/month = sustainable pace for founders | Command Your Brand 2026 |
| Transcript availability | Search for transcripts | Published transcripts = AI citation fuel | EvolveAMZ 2026 |
| Topic relevance | Search | Should address ICP-relevant problems | — |
| ICP alignment | Compare topics to ICP | Episodes about cost/tariffs > general sustainability | — |

**Note:** Podcast AI value has a 60-90 day lag (transcript indexing pipeline). Recent appearances won't show in AI yet.

**Scoring logic (0-10):**
- Existence: +0 if none, +2 if any appearances
- Volume: +0 if 1, +1 if 2-4, +2 if 5+
- Transcripts: +1 if auto-generated, +2 if published on company site
- Topic relevance: +1 if partially relevant, +2 if directly ICP-aligned
- ICP alignment: ×1.0 / ×0.5 / ×0.0

**What this improves when done well:**
- AI citation rate (5K-15K words of indexable content per episode, 15-30 brand mentions)
- Backlink profile (show notes link to site)
- Domain authority
- Branded search

---

### Industry Publications

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Any coverage | Search | Must have some | — |
| Contributed articles | Search | 2-4/year on DR 40+ sites = good | Industry |
| Earned coverage | Search | Press mentions, funding news, industry analysis | — |
| Publication authority | Search + DR check | DR 40+ = credible, DR 60+ = high authority | Ahrefs |
| ICP alignment | Compare article topics to ICP | Coverage should position company in ICP category | — |

**Note:** 96% of AI citations come from third-party sources, not brand-owned domains. Own blog does not count here.

**Scoring logic (0-10):**
- Existence: +0 if none, +2 if any third-party coverage
- Contributed: +1 if 1-2/year, +2 if 2-4/year, +3 if 4+
- Earned: +1 if any press, +2 if regular coverage
- Authority: +1 if any on DR 40+ sites, +2 if on DR 60+ sites
- ICP alignment: ×1.0 / ×0.5 / ×0.0

**What this improves when done well:**
- AI citation rate (third-party sources = AI trust)
- Domain authority (backlinks from high-DR sites)
- Branded search
- Direct referral traffic from readers

---

### Wikipedia / Wikidata

**What to check:**

| Signal | How to Check | Benchmark | Source |
|--------|-------------|-----------|--------|
| Wikipedia page | Search | Exists or doesn't | — |
| Wikidata entity | Search / SPARQL query | Exists or doesn't | Wikidata API |
| Notability signals | Search | Major funding, awards, press coverage precede Wikipedia | — |

**Scoring logic (0-10):**
- Wikipedia page: 10 points
- Wikidata entity only: 5 points
- Neither: 0 points

**Note:** Cannot be directly controlled. Companies cannot create their own Wikipedia page. Must be earned through notability. Wikidata entity can sometimes be created by the company.

**What this improves when done well:**
- AI entity recognition (massive boost)
- Knowledge Panel appearance
- Trust signals (users trust Wikipedia-vetted companies)

---

## Layer Score Calculation

Raw layer score = average of all platform scores (8 platforms × 0-10 each = max 80 points).

Normalize to 0-100: `layer_score = round(sum(scores) / 8 * 10)`.

Round to nearest integer.

---

## LLM Rubric Mapping

Each LLM-dependent check in this layer uses a rubric from [[llm-rubrics.md]].

| Check | Rubric | What the LLM Gets |
|-------|--------|-------------------|
| LinkedIn ICP alignment | Rubric 1 (ICP Alignment) | Company page description + ICP description |
| G2/Capterra category alignment | Rubric 1 (ICP Alignment) | Profile category + ICP description |
| YouTube third-party mentions | Rubric 1 (ICP Alignment) | Search results for brand on YouTube |
| Reddit sentiment | Rubric 3 (Sentiment & Quality) | Reddit post/comment text + subreddit context |
| Reddit content quality | Rubric 3 (Sentiment & Quality) | Reddit post/comment text + community context |
| Podcast appearance discovery | Rubric 4 (Podcast Discovery) | Search results + extracted content |
| Industry publication discovery | Rubric 4 adapted (same method, different source type) | Search results for brand in publications |

## Execution Method

1. For each platform, run web search + extract content where URLs found.
2. Deterministic checks run first (follower count, review count, video count, etc. via scraping or APIs).
3. LLM checks run second using the rubrics above. Each call receives the platform content + ICP description + rubric.
4. Scores computed using the per-platform scoring logic defined above.
5. Layer score = average of all 8 platform scores, normalized to 0-100.
6. Output: Structured JSON with per-platform scores, evidence, ICP alignment, improvement mapping, and recommendations.

---

## What This Layer Connects To

| Platform Score | Directly Improves |
|---------------|-------------------|
| LinkedIn | Branded search volume, outbound acceptance rate, retargeting pool |
| G2 / Capterra | AI citation rate, buyer trust, demo conversion, outbound reply rate |
| YouTube | AI citation rate (#1 signal), Google AI Overviews, organic search |
| Reddit | AI citation rate (Perplexity), corroboration threshold, branded search |
| Podcasts | AI citation rate, backlinks, domain authority, branded search |
| Publications | AI citation rate, domain authority, branded search |
| Wikipedia | AI entity recognition, Knowledge Panel, trust |

These feed directly into the acquisition model: better external presence → higher AI citations → more AI referral traffic → more discovery calls.
