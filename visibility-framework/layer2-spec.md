---
type: framework
layer: 2
topic: content-citability-audit
status: v2
created: 2026-05-20
updated: 2026-05-20
---

# Layer 2 — Content Citability Audit Specification

## What This Is

A repeatable specification for auditing a website's content for AI citability, search visibility, and conversion readiness. This is Layer 2 of the Trellace Visibility Framework.

**Executed by:** Parallel.ai Extract (get full page content) + deterministic code checks + LLM with rubric for E-E-A-T judgment and remediation drafts.

**Input:** URL, page list (from L1 crawl), ICP description, competitor URLs.

**Output:** Per-chunk scores, per-page scores, E-E-A-T assessment, remediation drafts, content coverage gaps, whole-site layer score.

---

## Core Principle

AI does not rank pages. It chunks content into ~134-167 word segments, embeds each chunk, and retrieves the most semantically similar ones. Layer 2 scores at the chunk level because that's where retrieval happens. A page with 5 excellent chunks and 15 terrible chunks is partially citable — not an average. We need to know which chunks work and which don't.

---

## Chunking Method

1. Extract full page content via Parallel.ai Extract (`full_content=true`). This replaces auditstack's 4000-character limit.
2. Strip navigation, footer, boilerplate (keep main content body).
3. Split into natural paragraphs first (respect existing structure).
4. For paragraphs outside 100-200 words: merge short ones, split long ones at sentence boundaries.
5. Add 15-20% content overlap between adjacent chunks.
6. Discard chunks that are purely navigation, cookie notices, or boilerplate (>50% nav/footer terms).

**Per-page sampling:**
- < 2,000 words: score all chunks
- 2,000-5,000 words: first 5 + last 3 + random sample of 5 middle
- > 5,000 words: first 5 + last 3 + random sample of 10 middle

---

## Deterministic Checks (Code — No LLM)

These are measured by pattern matching, regex, NER, counting, and HTML parsing. Based on llm-citeops methodology. No subjectivity.

### Chunk-Level

| Dimension | Method | Scoring |
|-----------|--------|---------|
| **Answer extractability** | Check first sentence of chunk: does it contain declarative pattern? ("is", "are", "means", "refers to", "works by") | 0-10: 10 if declarative answer in first 50 words with clear subject, 5 if declarative but vague, 0 if scene-setting or no answer present |
| **Factual density** | Regex: count numbers ($, %, dates, figures). NER: count named entities (companies, people, products). Stats per 100 words. | 0-10: `min(10, (entities + stats) / words * 100)`. 0-2 = 0-1 facts, 3-5 = 2-3 facts, 6-8 = 4-7 facts, 9-10 = 8+ facts per 100 words |
| **Self-containment** | Pattern match anti-patterns: "as mentioned above", "refer to", "click here", "see below", "previously discussed", unexplained pronouns at chunk start | 0-10: start at 10, subtract 2 per flag found |
| **Anti-citation flags** | Pattern match: CTA overload (>3 CTAs in chunk), keyword stuffing (same keyword >5 times), all-caps (>30% of text), boilerplate ratio >40%, thin content (<50 words) | 0-10: start at 10, subtract 1 per flag found |
| **Chunk word count** | Word count | Within 134-167: 10. 100-133 or 168-200: 7. 50-99 or 201-300: 4. <50 or >300: 1 |
| **Q&A density** | Count question marks + count of blocks under 100 words (likely answers). Ratio per 1000 words. | 0-10: ratio ≥ 5 = 10, 3-4 = 7, 1-2 = 4, 0 = 1 |

### Page-Level

| Dimension | Method | Scoring |
|-----------|--------|---------|
| **Flesch Reading Ease** | textstat library | 60-70 = 10, 50-59 = 8, 40-49 = 6, 30-39 = 4, <30 = 2. Target for B2B: 60-70. |
| **Word count** | Count | 1500-2500 = 10, 1000-1499 = 7, 500-999 = 4, <500 = 1. Pillar content: 2500-4000 = 10. |
| **Heading hierarchy** | HTML parse: H1→H2→H3, no skips | Clean = 10, one skip = 6, multiple skips = 3, no headings = 0 |
| **Lists presence** | HTML parse: bulleted/numbered lists exist? | 80%+ of cited pages use lists. Present = 10, absent = 3. |
| **URL slug quality** | Pattern: natural language vs opaque IDs | Natural language = 10 (89.78% citation rate), opaque = 5 (81.11% citation rate) |
| **Content freshness** | Date extraction from content + schema + headers | <90 days = 10, 90-180 = 6, 180-365 = 3, >365 or no date = 0 |
| **External citation count** | Count external links + named source mentions | 5+ external citations = 10, 2-4 = 7, 1 = 4, 0 = 1 |
| **Comparison content** | Detect "vs", "unlike", "compared to", "alternative to", "unlike [competitor]" | Present = 10, absent = 0 (binary — AI weights comparison content) |
| **Topical depth** | Heading count + unique H2 topics + word count signal | >10 headings with diverse topics = 10, 5-10 = 7, <5 = 4 |
| **Trust signals** | Detect HTTPS link, privacy policy link, contact page link, about page link in page content | 4 signals = 10, 2-3 = 7, 1 = 4, 0 = 1 |

---

## LLM Checks (With Rubric)

These require judgment. Every call uses the rubrics defined in [[llm-rubrics.md]].

| Check | Rubric | Input | Output |
|-------|--------|-------|--------|
| **E-E-A-T assessment** | Rubric 2: 20-item framework across Experience (5), Expertise (5), Authority (5), Trust (5). Pass/Partial/Fail per item. Veto system for critical failures. Content-type-specific weights. | Full page content + metadata | E-E-A-T score 0-100, dimension breakdown, veto status |
| **Citation worthiness** | Rubric 6: Anchored 0-10 scale. "Would an AI retrieve and cite this chunk?" with specific signal anchors. LLM must cite evidence. | Chunk text + page context | Score 0-10 with evidence |
| **Content coverage** | Rubric 1 (ICP Alignment): Compare site's topic coverage to ICP topics and competitor topics. | Full site page list + ICP + competitor URLs | Coverage gap report |
| **Remediation drafts** | Rubric 5: 30-80 word copy fixes for chunks scoring below threshold. Validated for length, tone, ICP language, factual verifiability. | Chunk text + problem type | Draft text + validation status |

---

## Per-Page Score Calculation

```
page_score = (
    0.30 × average_deterministic_chunk_score  (6 dimensions, code)
  + 0.20 × average_llm_chunk_score            (citation worthiness, LLM)
  + 0.15 × eeat_score                         (20-item rubric, LLM)
  + 0.20 × page_level_deterministic           (Flesch + word count + structure + freshness + citations + comparison + depth + trust)
  + 0.10 × content_type_extra                 (solution pages get +5 bonus for importance)
  + 0.05 × remediation_coverage              (% of low-score chunks that have remediation drafts)
) × 10  # normalize to 0-100
```

The split: 50% deterministic (chunk + page-level code checks), 35% LLM with rubric (citation worthiness + E-E-A-T), 15% content type context.

---

## Whole-Site Score

```
site_score = weighted_average(page_scores)
```

Weights:
- Solution/product pages: ×1.5
- Blog posts: ×1.0
- Case studies: ×1.3
- Utility pages (cookie policy, careers): ×0.3

---

## What This Layer Improves

| Signal | Directly Improves | Connection to Acquisition Model |
|--------|-------------------|-------------------------------|
| Chunk citability | AI citation rate | More AI referral traffic → more discovery calls |
| E-E-A-T signals | Google ranking, AI trust, conversion rate | More organic traffic + higher demo conversion |
| Factual density | AI retrieval weight (2-3× higher), backlinks | More AI citations + more referring domains |
| Content freshness | AI citation rate | 70%+ of cited pages updated in past year |
| Topic coverage | Google ranking breadth, AI citation breadth | More keywords ranking → more traffic → more calls |
| Comparison content | AI comparison query citations | Competitor displacement in AI |
| Remediation drafts | Speed to fix | Faster improvement → faster ROI |

---

## Validation & Calibration

1. **Spot-check 5-10 chunks per audit:** Compare deterministic scores to human judgment. Tune pattern thresholds if needed.
2. **Calibrate citation worthiness:** Compare LLM scores to actual Layer 4 citation results 8 weeks later. Chunks scored 8+ should get cited. Chunks scored 4- should not.
3. **Review veto triggers:** If the E-E-A-T veto fires on content that's actually fine, adjust rubric thresholds.

---

## Execution Method

1. Extract full page content via Parallel.ai Extract (`full_content=true`).
2. Chunk each page using the algorithm above.
3. Run deterministic checks on every sampled chunk.
4. Run LLM citation worthiness on every sampled chunk (Rubric 6).
5. Run E-E-A-T assessment per page (Rubric 2).
6. Run content coverage check across all pages (Rubric 1, ICP Alignment mode).
7. Generate remediation drafts for chunks below threshold (Rubric 5).
8. Calculate per-page and whole-site scores.
9. Output structured JSON + per-page breakdown + coverage gaps + remediation drafts.
