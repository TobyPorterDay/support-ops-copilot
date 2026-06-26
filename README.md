# Support Ops Copilot

> This project was built using Claude Code and a Claude chat.

A proof-of-concept pipeline for automatically classifying consumer financial complaints and generating an executive summary report. Built against publicly available CFPB complaint data.

## What it does

1. **Classify** (`classify.py`) — sends each complaint narrative to `claude-haiku-4-5-20251001` and returns a category, escalation risk (Low / Medium / High), and one-sentence reason, structured as JSON.
2. **Report** (`report.py`) — three-stage pipeline:
   - **Stage 1** (`compute_figures`) — pure Python; joins predictions with complaint metadata to produce a figures dict (counts, rates, top states).
   - **Stage 2** (`narrate`) — sends figures dict only (no raw text) to `claude-sonnet-4-6` and returns a structured executive summary.
   - **Stage 3** (`verify`) — audits every numeric token in the narrative against the figures dict; fails if any number cannot be sourced there.

## How to run

### Prerequisites

```
pip install anthropic python-dotenv
```

Copy `.env.example` to `.env` and add your Anthropic API key.

### Classify complaints

```
python classify.py
```

Reads `working_sample.csv` (CFPB export, not committed — see below), writes `predictions_full.csv`.

### Generate report

```
python report.py
```

Reads `predictions_full.csv` and `working_sample.csv` by default. To run against the committed eval set, edit the `PREDICTIONS_PATH` / `SAMPLE_PATH` constants at the top of `report.py`, or call `compute_figures()` directly with the paths you want.

## File guide

| File | Description |
|---|---|
| `classify.py` | Classifier — sends narratives to Haiku, returns category / risk / reason |
| `report.py` | Three-stage report generator (compute → narrate → verify) |
| `taxonomy_and_rubric.md` | v3 complaint category taxonomy and escalation rubric used in the system prompt |
| `labels.csv` | 56 hand-labeled complaints (category + risk); ground truth for the eval |
| `predictions_v3.csv` | Haiku predictions for the same 56 complaints; dollar amounts in `reason` redacted |
| `eval_results.md` | Eval metrics (precision, recall, missed/over-escalation) with the labels commit hash |
| `cost_analysis.md` | Token counts, cost projections, and cost-reduction levers |
| `.env.example` | Environment variable template |

## Taxonomy versions

The category taxonomy and escalation rubric evolved across three versions during the labeling and eval cycle.

| Version | Commit | What changed |
|---|---|---|
| v1 | `34c6ff7` | Initial taxonomy committed before labeling — 5 categories, Predatory included as a risk signal |
| v2 | `dc6c8d2` | Added Disputed/unauthorized account after pilot labeling revealed a failure type the original taxonomy missed |
| v3 | `19bdd0b` | Post-eval revision: dropped Predatory (severity flag, not a failure type), sharpened Closed-dispute vs Lack-of-action distinction, capped speculative harm at Medium, tightened High tiebreaker to realized harm only |

The current `taxonomy_and_rubric.md` is v3. All versions are recoverable via `git show <hash>:taxonomy_and_rubric.md`.

## Raw narratives

`complaints.csv` and `working_sample.csv` are excluded from this repository. They contain consumer complaint narratives sourced from the [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/), which is publicly available. Dollar amounts and specific timeframes in `predictions_v3.csv`'s `reason` column have been redacted (`$[redacted]`) to avoid re-identification from the public dataset.
