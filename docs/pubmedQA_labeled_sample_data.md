# PubMedQA `pqa_labeled` — real sample rows

Pulled directly from the locally downloaded dataset (not fabricated/web-scraped). These three rows illustrate the fields and, specifically, the **context vs. abstract** distinction raised while designing the corpus.

## Key distinction: `context` is NOT the full abstract

- `context.contexts` = the abstract's sections, **with the conclusion sentence removed**.
- `long_answer` = the conclusion sentence that was removed.
- **Full original abstract = `context` + `long_answer` stitched back together.**

This matters for two different pipeline stages:
- **Stage 1 (generation/extraction)**: the LLM should see only `context` — withholding the conclusion is the whole point of the task, forcing the model to infer the answer rather than read it.
- **Stage 2 (retrieval corpus)**: there's no reason to withhold the conclusion here, and doing so would hurt retrieval quality (conclusion sentences often contain the clearest matching language for a question). So the corpus should store the **full abstract** (`context` + `long_answer`), not `context` alone.

---

## Sample 1

- **pubid:** `21645374`
- **question:** Do mitochondria play a role in remodelling lace plant leaves during programmed cell death?
- **context sections:** `['BACKGROUND', 'RESULTS']`
- **context (truncated abstract, conclusion removed):**
  > Programmed cell death (PCD) is the regulated death of cells within an organism. The lace plant (Aponogeton madagascariensis) produces perforations in its leaves through PCD. The leaves of the plant consist of a latticework of longitudinal and transverse veins enclosing areoles. PCD occurs in the cel... *(truncated here for this doc; full text is longer)*
- **long_answer (the removed conclusion):**
  > Results depicted mitochondrial dynamics in vivo as PCD progresses within the lace plant, and highlight the correlation of this organelle with other organelles during developmental PCD. To the best of our knowledge, this is the first report of mitochondria and chloroplasts moving on transvacuolar str...
- **final_decision:** `yes`
- **full abstract (what goes in the retrieval corpus) = context + long_answer**

---

## Sample 2

- **pubid:** `16418930`
- **question:** Landolt C and snellen e acuity: differences in strabismus amblyopia?
- **context sections:** `['BACKGROUND', 'PATIENTS AND METHODS', 'RESULTS']`
- **context (truncated abstract):**
  > Assessment of visual acuity depends on the optotypes used for measurement. The ability to recognize different optotypes differs even if their critical details appear under the same visual angle. Since optotypes are evaluated on individuals with good visual acuity and without eye disorders, differenc...
- **long_answer (the removed conclusion):**
  > Using the charts described, there was only a slight overestimation of visual acuity by the Snellen E compared to the Landolt C, even in strabismus amblyopia. Small differences in the lower visual acuity range have to be considered.
- **final_decision:** `no`

---

## Sample 3

- **pubid:** `9488747`
- **question:** Syncope during bathing in infants, a pediatric form of water-induced urticaria?
- **context sections:** `['BACKGROUND', 'CASE REPORTS']`
- **context (truncated abstract):**
  > Apparent life-threatening events in infants are a difficult and frequent problem in pediatric practice. The prognosis is uncertain because of risk of sudden infant death syndrome. Eight infants aged 2 to 15 months were admitted during a period of 6 years; they suffered from similar maladies in the b...
- **long_answer (the removed conclusion):**
  > "Aquagenic maladies" could be a pediatric form of the aquagenic urticaria.
- **final_decision:** `yes`

---

## Takeaway for corpus construction

`pqa_labeled`, `pqa_artificial`, and `pqa_unlabeled` all have both `context` and `long_answer` (confirmed by checking feature schemas directly — only `final_decision` is subset-dependent: present in `labeled`/`artificial`, absent in `unlabeled`). So **every row across all three subsets can be reconstructed into a full abstract**, meaning the corpus can consistently store full abstracts (`context` + `long_answer`) regardless of which subset a document came from.
