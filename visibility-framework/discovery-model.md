---
type: framework
topic: visibility-to-discovery
status: v1
created: 2026-05-14
---

# Visibility → Discovery Calls Model

## What This Document Is

This connects the Visibility Framework to the metric clients actually care about: discovery calls. Every topic in the visibility framework is mapped to the specific discovery call source it feeds, with the intermediate effects that make the connection work.

**How to read this:** Each topic has tasks (A = binary, B = scalar, C = uncontrollable), plus what it improves, plus which discovery call sources it feeds, plus the conversion events it enables.

**How to use this with clients:** Start with the outcome they care about (more discovery calls). Walk backward through the sources. Show which topics feed each source. This turns "we need to fix your schema" into "we need to fix your schema because it's blocking the AI discovery calls you're already getting."

---

## Discovery Call Sources

These are the five distinct ways a prospect becomes a discovery call. Everything in the visibility framework feeds one or more of these:

| Source | What It Looks Like | Current State (Muir) |
|--------|-------------------|---------------------|
| **AI Referral** | Prospect asks ChatGPT/Perplexity about manufacturing cost software → Muir is cited → prospect clicks through → books demo | Already happening. Muir gets discovery calls from AI. Harris knows this works. |
| **Organic Search** | Prospect Googles "should cost modeling software" → Muir ranks → prospect visits site → books demo | Happening but unclear volume. Competes with aPriori, Costimator. |
| **Paid Search** | Prospect searches → sees Muir ad → clicks → lands on page → books demo | Happening if ads running. Efficiency depends on Quality Score (Layer 1). |
| **Outbound Email** | Muir sends email via Lemlist → prospect recognizes brand from AI/search/reviews → replies → books meeting | Happening. Warmer prospects reply more. |
| **LinkedIn / Social** | Prospect sees Muir post, team member content, or company page → visits profile/site → connects → conversation → demo | Happening. Harris is heavy on LinkedIn. |

---

## The Model: Topic → Effect → Source

### How to Read Each Topic Entry

```
TOPIC NAME (Layer X)
  What it is: One-sentence description
  A tasks: Binary things to check off
  B tasks: Scalar things to improve over time
  C items: Uncontrollable things to monitor
  What it improves: Specific effects this topic creates
  Discovery call sources fed: Which of the 5 sources this ultimately feeds
  Conversion events enabled: What step in the prospect journey this unlocks
  Why the client cares: How to explain this to Harris in one sentence
```

---

## Technical Foundation Topics (Layer 1)

### Topic: AI Crawler Access
**What it is:** Whether AI systems can read the website at all.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| GPTBot allowed in robots.txt | llms.txt quality (right pages, good descriptions) | CDN/WAF silently blocking AI bots |
| PerplexityBot allowed | llms-full.txt companion file exists | |
| ClaudeBot allowed | | |
| Google-Extended allowed | | |
| llms.txt file exists at domain root | | |
| Verified in server logs (bots actually reaching pages) | | |

**What it improves:** AI content indexability. Content being retrievable by RAG pipelines. Without this, nothing in Layer 2 matters for AI — the content can be perfect and still invisible.

**Discovery call sources fed:** AI Referral

**Conversion events enabled:** AI retrieves content → AI includes brand in answer → prospect clicks citation link → prospect visits site → prospect books demo

**Why the client cares:** "Right now, some of your discovery calls come from AI. If your robots.txt accidentally blocks AI crawlers, those calls stop overnight. We need to verify the door is open."


### Topic: Core Web Vitals
**What it is:** How fast, responsive, and stable the website feels to users.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| HTTPS with valid SSL | LCP < 2500ms (good) / 2500-4000 (ok) / > 4000 (bad) | Google algorithm changes to CWV weighting |
| XML sitemap submitted | INP < 200ms (good) / 200-500 (ok) / > 500 (bad) | |
| Canonical URLs correct | CLS < 0.1 (good) / 0.1-0.25 (ok) / > 0.25 (bad) | |
| Mobile responsive | TTFB < 200ms (good) | |
| 404 page with navigation | Mobile load < 3s (good) | |
| Breadcrumb navigation | | |
| Image width/height attributes set | | |
| Caching headers configured | | |

**What it improves:** Google ranking position (direct ranking factor). Quality Score in Google Ads (Landing Page Experience component). User experience → lower bounce rate → higher conversion rate. Page indexation efficiency.

**Discovery call sources fed:** Organic Search, Paid Search

**Conversion events enabled:** Page loads fast → user stays → user reads content → user clicks CTA → user books demo. Also: Landing Page Experience good → QS higher → CPC lower → more ad clicks for same budget → more landing page visits → more demos.

**Why the client cares:** "A slow site kills two things: your Google ranking (fewer people find you) and your ad costs (Google charges you more per click because your landing page is slow). Speed directly affects discovery call volume and ad spend."


### Topic: Schema & Structured Data
**What it is:** Machine-readable labels that tell search engines and AI what each piece of content means.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Organization schema (site-wide) | Schema completeness score (% of recommended types present) | |
| Article schema (blog posts) | | |
| FAQ schema (Q&A pages) | | |
| HowTo schema (tutorials) | | |
| SoftwareApplication schema (product pages) | | |
| BreadcrumbList schema (site-wide) | | |
| Zero errors in Google Rich Results Test | | |

**What it improves:** Rich snippet eligibility (Featured Snippets, FAQ accordions, product cards) → higher CTR from same ranking position. AI content parsing — schema tells AI what's a question, what's an answer, what's a product. Quality Score (structured data signals relevance). Entity recognition for Knowledge Graph.

**Discovery call sources fed:** Organic Search, AI Referral, Paid Search

**Conversion events enabled:** Rich snippet → higher CTR → more clicks from same impressions → more site visits → more demos. Schema → AI parses content correctly → more accurate AI citations → more AI referral traffic. Schema → QS improvement → lower CPC → more ad reach.

**Why the client cares:** "Schema is the label that tells Google and ChatGPT what your content actually is. Without it, your FAQ page is just text. With it, your FAQ page can appear as a rich snippet at the top of Google AND get cited by ChatGPT when someone asks about manufacturing costs. Same content, more discovery calls."


### Topic: Site Structure & Indexation
**What it is:** Whether search engines can find, crawl, and understand all pages on the site.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| No broken links or redirect chains | Internal linking: no orphan pages | Bing index behavior changes |
| Clean URL structure (natural language) | URL slug quality (89.78% citation rate for natural-language vs 81.11% for opaque) | |
| hreflang tags correct (if multi-language) | | |
| All images have alt text | | |

**What it improves:** Crawl efficiency → all content gets indexed → more pages eligible to rank. URL structure → higher AI citation probability. Internal linking → Google understands content hierarchy.

**Discovery call sources fed:** Organic Search, AI Referral

**Why the client cares:** "If Google can't find a page, it might as well not exist. We make sure every valuable page on your site is indexed and structured so both Google and AI can navigate it."

---

## Content Topics (Layer 2)

### Topic: Content Citability
**What it is:** Whether content is structured in a way AI systems can reliably extract and cite it.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Heading hierarchy exists (H1→H2→H3) | Chunk word count (134-167 words optimal) | AI model content weighting changes |
| Bulleted/numbered lists used | Answer placement (first 40-60 words) | Competitor content quality improvements |
| Content has visible last-updated dates | Chunk self-containment (reads standalone) | |
| Author bios present on content pages | Fact density (5+ entities/stats per 100 words) | |
| Sources cited for claims | Overall chunk citability score (Grade A-F) | |
| | Freshness (core pages < 90 days) | |

**What it improves:** AI citation rate — how often AI selects chunks from the site when answering relevant queries. Content in the 134-167 word range, self-contained, fact-dense, and answer-first is 2-3x more likely to be retrieved by RAG pipelines.

**Discovery call sources fed:** AI Referral, Organic Search

**Conversion events enabled:** AI query → RAG retrieves chunk → chunk is citable (right size, self-contained, fact-dense) → AI includes brand in answer → prospect clicks → discovery call.

**Why the client cares:** "The AI discovery calls you're already getting — they happen because AI found a chunk of your content and decided it was the best answer. We can make more of your content 'chunk-ready' so AI cites you more often. Same number of people asking AI questions, more of them finding Muir."


### Topic: E-E-A-T Content Quality
**What it is:** Whether content demonstrates Experience, Expertise, Authoritativeness, and Trustworthiness — Google's quality framework.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Author bios present | E-E-A-T rubric score (1-5 per pillar, avg ≥ 4.0) | |
| Sources cited | Trust score (anchor — must be ≥ 4.0) | |
| Case studies published | | |

**What it improves:** Google ranking (E-E-A-T is how Google evaluates content quality). AI trust — AI systems weight content from authoritative, well-sourced pages higher. Conversion rate — visitors who see expertise signals are more likely to trust and convert.

**Discovery call sources fed:** Organic Search, AI Referral, Outbound Email (prospects who research you find authoritative content → higher trust → higher reply rate)

**Why the client cares:** "When a prospect Googles you after getting your email, they need to find content that makes you look like the expert. E-E-A-T is the difference between 'these guys seem legitimate' and 'let me book a demo.'"


### Topic: Content Coverage
**What it is:** Whether the site covers all the topics and questions buyers search for.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Content pages exist for core keywords | Competitive coverage (90%+ of competitor topics covered) | |
| FAQ sections exist on relevant pages | Keyword-entity density (15+ entities per page) | |
| Meta titles/descriptions unique per page | Readability (Flesch 60-70) | |
| Clear CTA on every content page | | |

**What it improves:** Keyword ranking breadth — more pages ranking for more terms → more total organic traffic. AI citation breadth — more content covering more topics → cited for more query types.

**Discovery call sources fed:** Organic Search, AI Referral

**Why the client cares:** "Every question a buyer Googles about manufacturing costs that you don't have content for is a discovery call aPriori gets instead of you."


### Topic: Original Assets & Publications
**What it is:** Webinars, research, original data, transcripts — content that can't be found anywhere else.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Webinar transcripts published | Freshness of original data | |
| Original data/research published | | |
| Case studies with specific numbers | | |

**What it improves:** Backlink generation (original data gets cited by other sites). AI citation preference (AI weights unique data 2-3x higher than recycled content). E-E-A-T signals (original research = strongest experience signal).

**Discovery call sources fed:** Organic Search, AI Referral, Outbound Email (case studies as collateral), LinkedIn (shareable content)

**Why the client cares:** "Content that only exists on your site is the hardest for competitors to copy and the most valuable for AI. It's also what prospects share and what journalists cite."

---

## External Presence Topics (Layer 3)

### Topic: Review Site Presence (G2, Capterra, TrustRadius)
**What it is:** Profiles and reviews on the platforms B2B buyers use to evaluate software — and AI uses to verify brands.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| G2 profile claimed | G2: 60-80+ reviews, 4.5+ stars, 5-10 new/month | |
| Capterra profile claimed | Capterra: 50+ reviews, 4.0+ stars | |
| TrustRadius profile claimed | Profile completeness: 100% fields filled, screenshots, demo video | |
| Trustpilot profile claimed | | |
| Crunchbase profile accurate | | |

**What it improves:** AI inclusion gate — 100% of tools cited by ChatGPT have G2 profiles. Corroboration threshold — AI treats multiple review platforms saying similar things as verified truth. Direct discovery — buyers use G2/Capterra to shortlist vendors before contacting sales. Brand trust — prospects who find positive reviews are more likely to book a demo.

**Discovery call sources fed:** AI Referral, Organic Search (review sites rank for "[category] software"), Outbound Email (prospects check reviews before replying)

**Conversion events enabled:** AI query → AI checks review sites for brand verification → brand has reviews → AI includes brand in answer. Also: Prospect gets email → Googles brand → finds G2 reviews → sees 4.5 stars → replies and books meeting.

**Why the client cares:** "If you're not on G2, ChatGPT literally cannot see you as a real company for this category. And when a prospect Googles you after getting your email, the first thing they see is your reviews. Sixty 4.5-star reviews versus zero reviews is the difference between a reply and an ignore."


### Topic: YouTube Presence
**What it is:** Brand mentions in YouTube video transcripts — the single strongest correlation with AI visibility (0.737).

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| YouTube channel created | 1-2 videos/month, human-reviewed transcripts | Organic YouTube mentions by third parties |
| | Question-format titles, 3-5 paragraph descriptions | |

**What it improves:** AI citation rate — 29.5% of Google AI Overviews cite YouTube. YouTube mentions are the #1 predictor of AI brand visibility. Transcripts get indexed by Google and Bing, feeding both organic search and AI retrieval.

**Discovery call sources fed:** AI Referral, Organic Search (YouTube results appear in Google)

**Why the client cares:** "AI doesn't watch videos — it reads transcripts. Every time someone on YouTube says 'Muir AI' in a manufacturing context, that transcript becomes AI search fuel. YouTube is the most powerful visibility lever that most B2B companies completely ignore."


### Topic: LinkedIn Presence
**What it is:** Company page, team profiles, and thought leadership content on the platform where B2B buyers spend their professional attention.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Company page complete | Posting frequency: company 2-3/week, team 1-2/week each | |
| Team profiles complete (all key members) | Engagement rate: company 3-5%, individual 5-10% | |
| | Employee advocacy: 100% of team sharing content | |

**What it improves:** Brand awareness → branded search → domain authority → AI citations. Direct inbound — prospects can message or connect after seeing content. Outbound warmth — prospects who've seen the brand on LinkedIn are more likely to accept connection requests and reply to emails. Ad retargeting pool — more LinkedIn engagement = more retargetable contacts.

**Discovery call sources fed:** LinkedIn/Social, Outbound Email, Paid Search (through branded search lift), AI Referral (through brand awareness)

**Why the client cares:** "LinkedIn is where your buyers live. When you post, you're not just building a following — you're making every outbound email warmer and every retargeting ad more effective. A prospect who's seen three of your posts is not a cold lead anymore."


### Topic: Reddit & Community Presence
**What it is:** Genuine, non-promotional participation in communities where buyers discuss problems your product solves.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Reddit account exists | Active in 3-5 relevant communities | Organic Reddit mentions by third parties |
| Quora account exists | Comments helpful, not promotional | |

**What it improves:** AI citation rate — Reddit is 46.7% of Perplexity citations. AI treats Reddit as "real user sentiment." Corroboration — when AI finds brand mentions across multiple forums, it treats the brand as genuinely relevant.

**Discovery call sources fed:** AI Referral, Organic Search (Reddit threads rank in Google)

**Why the client cares:** "When someone on Reddit asks 'what's the best manufacturing cost software' and a genuine user mentions Muir, that Reddit thread becomes AI fuel for months. We can't control what people say — but we can make sure Muir is part of the conversation by being genuinely helpful in these communities."


### Topic: Third-Party Publications & Media
**What it is:** Industry articles, podcast appearances, conference talks — content on other people's platforms that references the brand.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Submitted to speak at conferences | Conference speaking: 2-4 talks/year | Conference acceptance |
| Pitched to podcasts | Podcast appearances: 4-6/year | Industry publication coverage |
| Pitched articles to publications | Contributed articles: 2-4/year on DR > 40 sites | Award selection |
| Award submissions sent | Industry association: active in 2-3, 1+ committee | |
| Industry association membership | | |

**What it improves:** Brand authority (96% of AI citations from third-party). Corroboration threshold — independent sources saying similar things. Direct traffic and leads from publication readers and podcast listeners. Backlinks from authoritative domains → domain authority → better Google rankings.

**Discovery call sources fed:** AI Referral, Organic Search, LinkedIn/Social (shareable third-party content)

**Why the client cares:** "The most powerful thing for AI visibility is other credible sources talking about you. Every podcast appearance, every industry article, every conference talk is a signal to AI that 'Muir AI is a real player in manufacturing cost estimation.' AI trusts third parties more than it trusts your own website — by design."


### Topic: Wikipedia & Entity Presence
**What it is:** Brand presence in knowledge bases and entity registries that AI systems use for verification.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Crunchbase profile accurate | | Wikipedia page creation |
| Google Knowledge Panel triggered | | |
| Partner/integration directory listings | | |

**What it improves:** Entity recognition — AI systems verify company existence through knowledge bases. Knowledge Panel → instant credibility when someone Googles the brand. Wikidata entries → feeds Google Knowledge Graph.

**Discovery call sources fed:** AI Referral, Organic Search

**Why the client cares:** "When ChatGPT mentions a company, it checks whether that company exists in knowledge bases. Being in those databases isn't optional — it's table stakes for AI visibility."

---

## Paid Amplification Topics (Layer 4)

### Topic: Google Ads Efficiency
**What it is:** How efficiently ad spend converts to discovery calls, and how visibility improvements lower the cost.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Google Ads account active | Quality Score ≥ 7 (weighted avg) | CPC market rates |
| Brand defense campaigns running | CTR: brand 15-25%, non-brand 3-8% | Competitor bid strategies |
| Conversion tracking configured | Conversion rate: demo/trial 5-10% | Platform algorithm changes |
| Bing Ads account active | CPC: below B2B SaaS avg ($5-7), decreasing | AI Overview impact on paid CTR |
| Landing pages for ad traffic | Landing page conversion: 5-15% | |

**What it improves:** Discovery call volume from paid sources. Cost per discovery call. ROAS.

**How visibility topics feed this:** Core Web Vitals → QS Landing Page Experience → lower CPC. AI citations → 91% more paid clicks on AI-heavy SERPs. Brand awareness from external presence → more branded searches → cheaper branded CPC. Schema → relevance signals → better QS.

**Why the client cares:** "Every point of Quality Score improvement is a discount on your ad spend. Every AI citation makes your ads more effective on the same page. Visibility isn't just about organic traffic — it directly reduces your cost per discovery call from paid."


### Topic: Outbound Email Performance
**What it is:** Lemlist sequences and their effectiveness at generating replies and meetings.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| Lemlist campaigns running | Open rate: 40-60% | |
| Sequences built for each campaign | Reply rate: 5-15% | |
| | Conversion rate: 1-3% to meeting | |

**What it improves:** Discovery call volume from outbound. Efficiency — more calls from same number of sends.

**How visibility topics feed this:** External presence → brand recognition → warmer prospects → higher open rate. Reviews → social proof → higher reply rate. AI citations → prospect has seen brand in AI → warmer → more likely to reply. LinkedIn presence → prospect recognizes name → accepts connection → replies.

**Why the client cares:** "An outbound email to someone who's never heard of you is spam. An outbound email to someone who saw Muir mentioned in ChatGPT last week is a follow-up. Visibility makes every email warmer."


### Topic: LinkedIn Ads
**What it is:** Paid amplification on LinkedIn, including retargeting.

| A — Binary | B — Scalar | C — Uncontrollable |
|------------|-----------|-------------------|
| LinkedIn Ads account active | Sponsored CTR: 0.3-0.6% | Platform algorithm changes |
| Retargeting audience configured | CPM: $6-9 for B2B SaaS US | |
| | Retargeting pool: 300+ (minimum), growing | |
| | Retargeting conversion: 0.3-0.8% | |

**How visibility topics feed this:** LinkedIn organic presence → engaged audience → retargeting pool grows. External presence → brand awareness → higher ad CTR. AI visibility → brand trust → higher conversion from ads.

---

## The Complete Connection Map

### Every Topic → Which Discovery Call Source It Feeds

| Topic | AI Referral | Organic Search | Paid Search | Outbound | LinkedIn |
|-------|:-----------:|:-------------:|:-----------:|:--------:|:--------:|
| AI Crawler Access | ● | | | | |
| Core Web Vitals | | ● | ● | | |
| Schema & Structured Data | ● | ● | ● | | |
| Site Structure & Indexation | ● | ● | | | |
| Content Citability | ● | ● | | | |
| E-E-A-T Content Quality | ● | ● | | ● | |
| Content Coverage | ● | ● | | | |
| Original Assets | ● | ● | | ● | ● |
| Review Sites (G2/Capterra) | ● | ● | | ● | |
| YouTube Presence | ● | ● | | | |
| LinkedIn Presence | ● | | | ● | ● |
| Reddit & Community | ● | ● | | | |
| Third-Party Publications | ● | ● | | | ● |
| Wikipedia & Entity | ● | | | | |
| Google Ads Efficiency | | | ● | | |
| Outbound Email | | | | ● | |
| LinkedIn Ads | | | | | ● |

### What This Table Means

A dot means: improving this topic directly feeds that discovery call source.

**Example:** Fixing AI Crawler Access (Layer 1) only feeds AI Referral directly. But AI Referral → more discovery calls → more revenue. And AI Crawler Access is a prerequisite for Content Citability to matter at all for AI. So it's essential even though it only feeds one source.

**Example:** Schema feeds three sources: Organic Search (rich snippets → higher CTR), AI Referral (AI can parse content), and Paid Search (signals feed into Quality Score). One fix, three discovery call sources improved.

---

## The Assumptions We're Making (To Be Validated)

1. **AI referral already drives discovery calls for Muir.** Harris has confirmed this. This is not an assumption — it's observed.

2. **Improving AI visibility increases AI-driven discovery calls.** Logical: more AI citations = more AI referral traffic = more discovery calls. But we need to measure the conversion rate of AI traffic specifically.

3. **External presence improves outbound reply rates.** Logical: warmer prospects reply more. But we don't yet have data on how much G2 reviews or YouTube mentions lift reply rates vs a control group.

4. **Quality Score improvements translate to measurable CPC savings.** Well-documented: QS 8 vs QS 4 = 47% lower CPC. This is Google's published mechanics, not an assumption.

5. **Content citability improvements increase AI citation rate.** Supported by the KDD 2024 GEO study (statistics → ~41% visibility improvement). But the magnitude for Muir specifically is unknown until tested.

---

## Next: Quantification

This document defines the connections qualitatively — "this helps that." The next step is to put numbers on the connections:

- If AI citations increase by X%, how many more AI-driven discovery calls?
- If outbound reply rate increases by Y%, how many more meetings?
- If Quality Score goes from 5 to 7, how much CPC savings?

That quantification layer is what turns this from a connection map into a business case. But the qualitative map comes first — because if the logic doesn't hold, the numbers don't matter.

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-05-14 | v1 | Initial topic-to-discovery model. Maps 17 topics to 5 discovery call sources. |
