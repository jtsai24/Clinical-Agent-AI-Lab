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
`output/` itself is gitignored — when a run is worth showcasing in this README, its
run JSON + generated HTML are copied into [`selected_output/runs/`](selected_output/runs/),
which *is* committed and served live via [GitHub Pages](https://jtsai24.github.io/Clinical-Agent-AI-Lab/)
(repo root, `main` branch — GitHub's `blob` view only shows HTML as source, never renders it).

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

100-row model comparison across providers, via `scripts/run_model_comparison.py`
(#19; original 10-row sweep in [#11](../../issues/11)). Each row links to its full
per-row HTML report ([#15](../../issues/15)), served live via GitHub Pages; the
underlying run JSON + HTML for this specific comparison are checked into
[`selected_output/runs/`](selected_output/runs/) — everyday runs still go to
`output/` (gitignored) and get copied here only when curated for the README:

| Model | Accuracy | Valid / rejected | Avg latency/row | Total cost | Report |
|---|---|---|---|---|---|
| deepseek-ai/DeepSeek-V4.1-Flash-1017 | 71% | 98 / 2 | 1.29s | $0.0649 | [html](https://jtsai24.github.io/Clinical-Agent-AI-Lab/selected_output/runs/2026-11-08T17-10-10_deepseek-ai_DeepSeek-V4.1-Flash-1017.html) |
| zai-org/GLM-5.3-Flash | 74% | 99 / 1 | 2.47s | $0.0274 | [html](https://jtsai24.github.io/Clinical-Agent-AI-Lab/selected_output/runs/2026-11-08T17-10-39_zai-org_GLM-5.3-Flash.html) |
| zai-org/GLM-5.3 (full) | 76% | 95 / 5 | 3.31s | $0.2789 | [html](https://jtsai24.github.io/Clinical-Agent-AI-Lab/selected_output/runs/2026-11-08T17-11-31_zai-org_GLM-5.3.html) |
| moonshotai/Kimi-K3.1-Pro | 77% | 96 / 4 | 10.92s | $0.6465 | [html](https://jtsai24.github.io/Clinical-Agent-AI-Lab/selected_output/runs/2026-11-08T17-12-53_moonshotai_Kimi-K3.1-Pro.html) |
| openai/gpt-oss-120b | 75% | 100 / 0 | 2.09s | $0.0217 | [html](https://jtsai24.github.io/Clinical-Agent-AI-Lab/selected_output/runs/2026-11-08T17-16-39_openai_gpt-oss-120b.html) |

`GLM-5.3-Flash` is kept as the model going forward: at n=100 all five models converge
into a tight 71-77% band (unlike #11's original 10-row sweep, which spread 40-70% —
mostly sampling noise, not a real model gap: DeepSeek alone jumped from 40% to 71%
between the 10- and 100-row runs). Flash gets within 2-3 points of the top (Kimi, 77%)
at roughly 1/4 the latency and 1/24 the cost per row.

At n=100, far more rows than #11's original three fail across nearly every model: 10
rows are mismatched in all 5 models, 20 in at least 4 of 5 (vs. the 3 rows #11 found at
n=10). This strengthens #11's underlying point rather than changing it — the dataset's
own 2019 baseline prediction also misses several of these same rows — see #11 for why
this points at a hard-to-extract signal in the withheld-conclusion context rather than
a shared reasoning gap, and why Stage 1's accuracy numbers measure reasoning-from-partial-evidence,
not real-world "can the LLM answer given the full paper" utility.

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
      - [**#20 — Showcase curated run outputs via selected_output/, tracked in git**](../../issues/20) — `active`
        — output/ is gitignored, so README-linked HTML reports need a committed, hand-curated copy
    - [**#4 — Stage 2 (retrieval)**](../../issues/4) — `DEFERRED` until #7 is done
      — 7-step corpus + vector DB + recall@k plan, sampling-strategy decision

**Convention for superseding an issue:** close it with a comment stating what replaced it, explicitly calling out whether it's *deprecated* (replaced, not completed) vs. genuinely done. "Closed" alone means completed; a replaced issue's close comment must say so.

**Convention for deferring an issue:** leave it open, but note in the README tree (here) and in the issue itself what it's waiting on, so "open" doesn't get read as "in progress."
