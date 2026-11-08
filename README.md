# Clinical Agent AI Lab

Hands-on prep for two Orphic Health interviews (Agentic Engineering, Nov 10; AI System Design, Nov 12) — and the start of a real, evaluated clinical LLM project beyond them. Uses PubMedQA to build two independently testable stages: LLM extraction/reasoning over given evidence (Stage 1), and retrieval of the right evidence from a larger corpus (Stage 2). See [#2](../../issues/2) for the full rationale and the formal Stage 1/Stage 2 definitions.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py   # caches PubMedQA locally (~545MB, one-time)
```

## How to run it

```bash
# sequential, 10 rows by default (edit ROW_COUNT in the script to change)
python scripts/call_llm.py

# concurrent (#16), configurable
python scripts/call_llm_concurrent.py --rows 50 --workers 5
```

Both write one JSON file per row to `output/raw/` and one aggregate run file to
`output/runs/<timestamp>_<model>.json` (row records + the aggregate report: accuracy,
valid/rejected/errored counts, rejected-by-reason, mismatches, latency, cost).

```bash
# render a run as a browsable HTML report (#15)
python scripts/generate_report.py output/runs/<timestamp>_<model>.json

# run the same row slice across every model in MODELS, one call_llm_concurrent.py
# subprocess per model — a model failing doesn't abort the rest of the sweep (#18)
python scripts/run_model_comparison.py --rows 10 --workers 5

# compare accuracy/latency/cost across every saved run, plus a per-model
# accuracy-over-time sparkline (#14, #18)
python scripts/compare_runs.py
```

Requires `MODEL_PROVIDER`, `MODEL_BASE_URL`, `MODEL_NAME` in `.env` and `MODEL_API_KEY`
in `.env.secret` (see [#12](../../issues/12), [`docs/api_key_handling.md`](docs/api_key_handling.md)).

## Results

Latest 50-row run, `zai-org/GLM-5.3-Flash`, 5 concurrent workers (#16):

- **83.7% accuracy** (49 valid / 1 rejected [`malformed_json`] / 0 errored)
- ~21.9s wall clock, ~2.1s avg latency/row, ~$0.014 total cost

10-row model comparison across providers, re-run via `scripts/run_model_comparison.py`
(#18; original sweep in [#11](../../issues/11)):

| Model | Accuracy | Avg latency/row | Total cost |
|---|---|---|---|
| deepseek-ai/DeepSeek-V4.1-Flash-1017 | 40% | 1.46s | $0.0068 |
| zai-org/GLM-5.3-Flash | 70% | 2.37s | $0.0025 |
| zai-org/GLM-5.3 (full) | 50% | 2.69s | $0.0280 |
| moonshotai/Kimi-K3.1-Pro | 67% | 24.09s | $0.1052 |
| openai/gpt-oss-120b | 60% | 2.46s | $0.0022 |

`GLM-5.3-Flash` is kept as the model going forward: best accuracy of the five, and
roughly 10-40x cheaper and faster per row than the two next-best (Kimi, GLM-5.3 full).
Exact percentages shift a few points run-to-run (compare to #11's original 40/70/60/70/60
despite `temperature=0`) — the direction (DeepSeek weakest, Flash/gpt-oss mid-to-strong,
Kimi accurate but far slower/pricier) is the stable signal, not the exact numbers.
Three rows (`17208539`, `26037986`, `26852225`) failed across nearly every model tested,
including the dataset's own 2019 baseline prediction — see #11 for why this points at a
hard-to-extract signal in the withheld-conclusion context rather than a shared reasoning
gap, and why Stage 1's accuracy numbers measure reasoning-from-partial-evidence, not
real-world "can the LLM answer given the full paper" utility.

## Production gaps

This is a rehearsal/prototype, not a production deployment. Known gaps, tracked in
detail in [`production_gaps.md`](production_gaps.md):

- **Secrets handling** — local `.env`/`.env.secret` files today; a real deployment
  would hold the API key in a managed secrets store (encrypted at rest, access-logged,
  rotated), since the LLM provider boundary can't support short-lived auto-issued
  credentials the way internal service-to-service calls can.
- **No retries/backoff/rate limiting** on LLM calls beyond catching `RateLimitError`
  into an `error` status.
- **Only a 50-row eval cap** — no larger-scale accuracy measurement.
- **No PHI handling** — this uses only public PubMedQA abstracts; real patient data
  would need a BAA with the model provider and audit logging of what was sent.
- **No monitoring/alerting** on reject rate or accuracy drift, and no human review
  workflow for rejected rows.

## Reference docs

Plan and production-tracking docs live at the repo root since they're actively edited during the build; everything else is reference material, under [`docs/`](docs/):

- [`PLAN.md`](PLAN.md) — Stage 1 plan: clarifying questions, inputs/outputs, what "correct" means
- [`docs/datasets.md`](docs/datasets.md) — dataset options considered before choosing PubMedQA
- [`docs/pubmedQA_labeled_sample_data.md`](docs/pubmedQA_labeled_sample_data.md) — real sample rows, annotated
- [`docs/example_reasoning_walkthrough.md`](docs/example_reasoning_walkthrough.md) — one full example reasoned through in plain language
- [`docs/interview_prep_reading_list.md`](docs/interview_prep_reading_list.md) — how interviewers score working with coding agents
- [`docs/api_key_handling.md`](docs/api_key_handling.md) — API key handling: why env vars while prototyping, and the production-tier distinction
- [`production_gaps.md`](production_gaps.md) — where rehearsal/prototype choices (e.g. secrets handling) diverge from production practice

## How the issues fan out

Issues are the project's decision log — why something was chosen, what was discovered, what's planned. They form a tree, not a flat list: [#2](../../issues/2) is the root, everything else branches off it as either dataset groundwork or build-plan work.

- [**#2 — Project direction: why build this**](../../issues/2) — `ROOT` · active, canonical reference
  - Why this project exists, the two interviews, long-term goal, and the formal Stage 1 / Stage 2 definitions.
  - **Dataset deep dive**
    - [**#1 — Project goal and dataset decision**](../../issues/1) — `DEPRECATED`, split into #2 + #3
    - [**#3 — Dataset analysis**](../../issues/3) — `active`
      — options considered, why PubMedQA, fallback plan, scoping decisions (abstract-only RAG, question-from-title caveat)
    - [**#5 — Dataset download mechanics**](../../issues/5) — `active`
      — download code, local cache location/size, `reasoning_*_pred` discovery
    - [**#6 — Deep dive: dataset structure**](../../issues/6) — `active`
      — stable reference for what's in PubMedQA: subset schemas, context vs. full-abstract distinction
  - **Build plan**
    - [**#7 — Stage 1 (extraction, interview rehearsal)**](../../issues/7) — `ACTIVE`, current work
      — rehearsal-oriented plan for the Agentic Engineering interview
      - [**#8 — Stage 1: credential handling for the Together API key**](../../issues/8) — `active`
        — decisions, mechanism, and OS-level reasoning for the `.env`/env-var approach
      - [**#9 — Add a validation layer**](../../issues/9) — `active`
        — `scripts/validate.py`: parsing/rejecting malformed LLM responses before scoring
      - [**#10 — Aggregate reporting: what we report and how**](../../issues/10) — `active`
        — accuracy, reject/error breakdowns, mismatches; `scripts/aggregate.py`
      - [**#11 — Model comparison results**](../../issues/11) — `active`
        — 10-row comparison across 5 models, and the reasoning-vs-utility limitation
      - [**#12 — Split the API key into its own file**](../../issues/12) — `active`
        — `.env` (non-secret config) vs `.env.secret` (API key only)
      - [**#13 — Unit tests for validate/score/aggregate**](../../issues/13) — `active`
        — 21/21 passing, includes the step 4 break-a-test exercise
      - [**#14 — Latency/cost tracking and cross-run comparison**](../../issues/14) — `active`
        — per-call latency/cost fields; `scripts/compare_runs.py`
      - [**#15 — HTML report for a single run**](../../issues/15) — `active`
        — `scripts/generate_report.py`, renders `output/runs/*.json` to a browsable report
      - [**#16 — Concurrent LLM calls via ThreadPoolExecutor**](../../issues/16) — `active`
        — `scripts/call_llm_concurrent.py`, N=5 default, `--rows`/`--workers` flags
      - [**#17 — Rename report.py to aggregate.py**](../../issues/17) — `active`
        — naming cleanup discovered mid-build; own issue and commit per the standing convention
      - [**#18 — Accuracy-over-time sparkline in compare_runs.py**](../../issues/18) — `active`
        — per-model trend view across saved runs, no new dependency
      - [**#19 — --model flag + run_model_comparison.py sweep script**](../../issues/19) — `active`
        — re-ran the #11 model comparison with runs actually saved to output/runs/
    - [**#4 — Stage 2 (retrieval)**](../../issues/4) — `DEFERRED` until #7 is done
      — 7-step corpus + vector DB + recall@k plan, sampling-strategy decision

**Convention for superseding an issue:** close it with a comment stating what replaced it, explicitly calling out whether it's *deprecated* (replaced, not completed) vs. genuinely done. "Closed" alone means completed; a replaced issue's close comment must say so.

**Convention for deferring an issue:** leave it open, but note in the README tree (here) and in the issue itself what it's waiting on, so "open" doesn't get read as "in progress."
