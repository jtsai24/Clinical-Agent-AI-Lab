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

Issues are the project's decision log — why something was chosen, what was discovered, what's planned. They form a tree, not a flat list: [#2](../../issues/2) is the root, everything else branches off it as either dataset groundwork or build-plan work.

[**#2 — Project direction: why build this**](../../issues/2) &nbsp;*[ROOT — active, canonical reference]*<br>
&nbsp;&nbsp;&nbsp;Why this project exists, the two interviews, long-term goal, and the formal Stage 1 / Stage 2 definitions.<br>
<br>
&nbsp;&nbsp;├── **Dataset deep dive**<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── [**#1 — Project goal and dataset decision**](../../issues/1) &nbsp;*[DEPRECATED — split into #2 + #3]*<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── [**#3 — Dataset analysis**](../../issues/3) &nbsp;*[active]*<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;Options considered, why PubMedQA, fallback plan, scoping decisions (abstract-only RAG, question-from-title caveat)<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── [**#5 — Dataset download mechanics**](../../issues/5) &nbsp;*[active]*<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;Download code, local cache location/size, reasoning_*_pred discovery<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── [**#6 — Deep dive: dataset structure**](../../issues/6) &nbsp;*[active]*<br>
&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Stable reference for what's in PubMedQA — subset schemas, context vs. full-abstract distinction<br>
&nbsp;&nbsp;│<br>
&nbsp;&nbsp;└── **Build plan**<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── [**#7 — Stage 1 (extraction, interview rehearsal)**](../../issues/7) &nbsp;*[ACTIVE — current work]*<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;Rehearsal-oriented plan for the Agentic Engineering interview<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── [**#4 — Stage 2 (retrieval)**](../../issues/4) &nbsp;*[DEFERRED until #7 is done]*<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;7-step corpus + vector DB + recall@k plan, sampling-strategy decision<br>

**Convention for superseding an issue:** close it with a comment stating what replaced it, explicitly calling out whether it's *deprecated* (replaced, not completed) vs. genuinely done. "Closed" alone means completed; a replaced issue's close comment must say so.

**Convention for deferring an issue:** leave it open, but note in the README tree (here) and in the issue itself what it's waiting on, so "open" doesn't get read as "in progress."
