# Classifier Cost Analysis

## Measured (pilot)

| Run | Rows | Estimated cost | Per ticket |
|---|---|---|---|
| v3 (Haiku 4.5) | 56 | ~$0.06 | ~$0.001 |

## Cost structure

Input-dominated: ~90% of tokens are the narrative + rubric system prompt; output is ~60 tokens of JSON per row and is essentially free at $5/MTok.

## Projections (uncached, standard pricing)

| Scale | Weekly tickets | Estimated cost |
|---|---|---|
| Pilot → production | 500 | ~$0.54 |
| 10× scale | 5,000 | ~$5.40 |

## Optimization levers

### 1. Batches API — immediate, zero rework (50% discount)

The weekly classification job is async by nature (batch of tickets, results consumed later). The Batches API applies a flat 50% discount with no prompt restructuring required.

- 500-ticket weekly report: **$0.54 → $0.27**
- 5,000 tickets/week: **$5.40 → $2.70**

### 2. Prompt caching — blocked on Haiku 4.5 as-is

Haiku 4.5's minimum cacheable prefix is **4,096 tokens**. The v3 system prompt is ~508 tokens, well below the threshold. Caching does not apply without significant prompt expansion.

### 3. Few-shot examples + caching — future v4 lever

Adding 5–10 labeled few-shot examples to the system prompt would:
- Push the prompt past the 4,096-token minimum, unlocking cache reads (~10% of input cost per cached token)
- Directly improve Medium/High accuracy (the confusion matrix shows the model collapses too many Medium cases to High)
- Constitute the v4 taxonomy update

This is the right lever after the eval loop stabilises, not before.

## Model tier rationale

**Classification layer → Haiku 4.5.** The task is structured (five categories, three risk tiers, JSON output) and the rubric provides all necessary signal. Haiku handles it adequately at $1/$5 per MTok.

**Narrative/summary layer → Sonnet 4.6.** Drafting agent-facing case summaries, escalation rationales, or customer-facing responses requires stronger prose and reasoning. Sonnet 4.6 at $3/$15 per MTok is the right tier for that layer — kept separate so classification cost stays low.
