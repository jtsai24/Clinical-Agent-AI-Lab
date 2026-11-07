# Clinical Agent AI Lab

Hands-on prep for two Orphic Health interviews (Agentic Engineering, Nov 10; AI System Design, Nov 12) — and the start of a real, evaluated clinical LLM project beyond them. Uses PubMedQA to build two independently testable stages: LLM extraction/reasoning over given evidence (Stage 1), and retrieval of the right evidence from a larger corpus (Stage 2). See [#2](../../issues/2) for the full rationale and the formal Stage 1/Stage 2 definitions.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_data.py   # caches PubMedQA locally (~545MB, one-time)
```

## Reference docs

- [`datasets.md`](datasets.md) — dataset options considered before choosing PubMedQA
- [`pubmedQA_labeled_sample_data.md`](pubmedQA_labeled_sample_data.md) — real sample rows, annotated
- [`example_reasoning_walkthrough.md`](example_reasoning_walkthrough.md) — one full example reasoned through in plain language
- [`interview_prep_reading_list.md`](interview_prep_reading_list.md) — how interviewers score working with coding agents

## How the issues fan out

Issues are the project's decision log — why something was chosen, what was discovered, what's planned. Since issues sometimes get replaced as understanding evolves, this table is the map of what's current.

| # | Title | Status | Role |
|---|---|---|---|
| [#1](../../issues/1) | Project goal and dataset decision | **Deprecated** — superseded by #2 + #3 | Original combined issue, split once it became clear direction and dataset choice needed separate tracking |
| [#2](../../issues/2) | Project direction: why build this | Active — canonical reference | Why this project exists, the two interviews, long-term goal, and the formal **Stage 1 / Stage 2 definitions** |
| [#3](../../issues/3) | Dataset analysis | Active | Options considered, why PubMedQA, fallback plan, scoping decisions (abstract-only RAG, question-derived-from-title caveat) |
| [#4](../../issues/4) | Build plan: Stage 2 (retrieval) | Active | 7-step corpus + vector DB + recall@k plan, sampling-strategy decision |
| [#5](../../issues/5) | Dataset download mechanics | Active | Download code, local cache location/size, `reasoning_*_pred` field discovery |
| [#6](../../issues/6) | Deep dive: dataset structure | Active | Stable reference for what's actually in PubMedQA — subset schemas, `context` vs. full-abstract distinction |
| [#7](../../issues/7) | Build plan: Stage 1 (extraction, as interview rehearsal) | Active | Rehearsal-oriented build plan for the Agentic Engineering interview, grounded in the reading list |

**Convention for superseding an issue:** close it with a comment stating what replaced it, explicitly calling out whether it's *deprecated* (replaced, not completed) vs. genuinely done. "Closed" alone means completed; a replaced issue's close comment must say so.
