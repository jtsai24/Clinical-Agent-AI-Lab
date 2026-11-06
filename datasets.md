# Candidate Datasets

Backup dataset options, grouped by the kind of pipeline they support. All are free; credentialed ones are flagged.

## Ready to use: labeled, open, quick to download

| Dataset | What it is | Pipeline it fits | Answer key |
|---|---|---|---|
| **PubMedQA** (`qiaojin/PubMedQA` on HF) | 1k expert-labeled question + abstract pairs | LLM extraction / RAG | yes/no/maybe |
| **BC5CDR** (HF `bigbio/bc5cdr`) | 1,500 PubMed abstracts annotated with chemicals, diseases and chemical→disease relations | **Entity extraction**: text → `{drugs, diseases, relations}` | Gold entities, so precision/recall |
| **NCBI-Disease** (HF `bigbio/ncbi_disease`) | ~800 abstracts with disease mentions | Simpler entity extraction | Gold spans |
| **MedQA (USMLE)** | Board-exam multiple-choice questions | LLM reasoning eval, model leaderboard | Correct option |
| **MedMCQA** | ~190k medical exam MCQs with explanations | Same, at scale | Correct option |
| **RAGBench** (`rungalileo/ragbench`, subsets `pubmedqa`, `covidqa`) | Question + retrieved docs + response + labels | RAG / hallucination eval | Relevance, adherence labels |
| **BioASQ** | Biomedical QA with gold PubMed docs and snippets | RAG with retrieval gold | Answers + gold docs (free registration) |

## Unstructured text, no labels (you make a small answer key)

| Dataset | What it is | Good for |
|---|---|---|
| **EPFL Clinical Guidelines** (`epfl-llm/guidelines`) | ~37k guideline articles (WHO, NICE, CDC…) | **Closest to Orphic.** Extract recommendations → JSON; hand-label 20 |
| **MTSamples** (Kaggle "medical transcriptions") | ~5k transcribed clinical notes with specialty tags | Note → structured fields (meds, diagnoses); specialty label gives a free classification check |
| **ClinicalTrials.gov API** | Trial records with free-text eligibility criteria | Criteria → structured `{age, conditions, exclusions}`; very realistic extraction task |

## Synthetic patient data (no privacy concerns)

| Dataset | What it is | Good for |
|---|---|---|
| **Synthea** | Synthetic patient records, including **FHIR** JSON | `get_patient_data` tool for the agentic design; FHIR → flat tables ETL |

## Gold standard but credentialed (skip this week)

- **MIMIC-IV / MIMIC notes, MedNLI, emrQA, n2c2:** real clinical notes, but access requires PhysioNet credentialing and training, which takes days to weeks. Good to **name** in the System Design interview ("for real eval I'd use MIMIC under a data use agreement"), not to build with now.

## If PubMedQA doesn't work out

1. **BC5CDR** is a different shape of task, extraction instead of QA, and the metrics (precision/recall/F1) are a good thing to practice.
2. **EPFL guidelines + 20 hand-labeled recommendations** is the most Orphic-like, but costs about an hour of labeling.
3. **MTSamples** is the messiest real-looking clinical text, good for practicing validation.

The Hugging Face IDs are from memory — verify them when downloading. The datasets themselves are well established.
