# PLAN: Stage 1 — PubMedQA extraction pipeline

Plan for [#7](../../issues/7), written before any pipeline code, per the issue's step 1.

## Clarifying questions and answers

1. **Which subset?** → `pqa_labeled` only. It's the only subset with expert-annotated `final_decision`; `pqa_artificial`'s labels are heuristically generated, too noisy for a scored rehearsal. `pqa_unlabeled` has no label at all.
2. **What is `evidence_quote`, and how strictly must it match?** → It's not a dataset field — the LLM generates it as part of its structured output (`{answer, evidence_quote}`), citing the sentence(s) in `context` it's basing its answer on. We validate it with a case-insensitive, whitespace-normalized substring check against `context`. This catches real fabrication (a quote that isn't in the abstract at all) without rejecting a genuine quote over harmless formatting drift (extra spaces, capitalization).
3. **What counts as a valid `answer` value?** → Exactly `yes`, `no`, or `maybe` (case-insensitive), matching `final_decision`'s own value domain. Anything else is a validation reject, not a wrong answer — kept in a separate bucket from scoring mismatches.
4. **Which LLM, and how are credentials handled?** → Together AI, `meta-llama/Llama-3.3-70B-Instruct-Turbo` — same provider/model already validated end-to-end in [flyte-open-model-factory#3](https://github.com/jtsai24/flyte-open-model-factory/issues/3). This project uses its *own* API key (not shared with that repo, to keep blast radius and rate limits isolated), stored in a local `.env` (gitignored, `chmod 600`), loaded at runtime via `python-dotenv` rather than manual shell sourcing — fewer steps to forget mid-interview. A less rigidly JSON-reliable open model is an acceptable tradeoff here since `malformed_json` is already a tracked reject code, not an unhandled failure.

## Inputs

- `pqa_labeled` rows, each with: `pubid`, `question`, `context` (abstract sections, conclusion withheld — see [pubmedQA_labeled_sample_data.md](docs/pubmedQA_labeled_sample_data.md)), `final_decision` (gold label).
- Start with 5-10 rows (first slice, inspected by eye), cap at 50 for the full run.
- `temperature=0` for every LLM call; raw responses saved alongside parsed output for auditability.

## Process

1. Load row → build prompt from `question` + `context`.
2. Call LLM → parse JSON response into `{answer, evidence_quote}`.
3. Validate:
   - JSON parses and has both fields → else reject `malformed_json`.
   - `answer` ∈ {yes, no, maybe} → else reject `invalid_answer`.
   - `evidence_quote` is non-trivial (not empty, not a near-duplicate of the whole context) → else reject `trivial_quote`.
   - `evidence_quote` found in `context` via normalized substring match → else reject `fabricated_quote`.
   - `context` itself present and non-empty → else reject `missing_context` (should not occur with this dataset, but checked since nothing upstream guarantees it).
4. Valid rows only: compare `answer` to `final_decision` → `correct` or `mismatch`.

## Outputs

- Per-row record: `pubid`, `question`, `answer`, `evidence_quote`, `final_decision`, `status` (`valid`/`rejected`), `reject_reason` (if rejected), `correct` (bool, valid rows only), raw LLM response.
- Aggregate report: total rows in, valid count, rejected count by reason, accuracy over valid rows, list of mismatches (`pubid` + both answers) for manual review.
- Row accounting must reconcile: `in = valid + rejected`.

## What "correct" means

A row is correct only if it's `valid` (passed all checks above) **and** `answer` exactly matches `final_decision`. A row that was rejected is never counted as correct or incorrect — it's excluded from accuracy and reported separately, so a fabricated-evidence row that happened to guess the right `answer` doesn't inflate the score.

## Next steps after this plan

1. Tiny slice (5-10 rows) end to end, inspect output by eye.
2. Tests on risky parts: malformed JSON, invalid answer, fabricated/trivial quote, missing context, row accounting.
3. Break one test on purpose, watch it fail, fix it.
4. Scale to 50 rows, write up results + production gaps in README.
