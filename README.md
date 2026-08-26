# FinGap-Governance

Replication materials for the paper *"FinGap-Governance: A
Traceability-Centric Framework for Diagnosing Isomorphic Regulatory Blind
Spots in Financial LLMs across Anomaly Detection, Advisory, and
Accounting Tasks."*

> **Anonymized for peer review.** Author, affiliation, and venue
> information has been removed in accordance with double-blind review
> requirements. This notice will be replaced with full metadata upon
> acceptance.

This repository contains the schema-audit and illustrative-walkthrough
code that supports the paper's existence-proof evidence. It does **not**
contain large-scale quantitative measurement or full dataset labeling,
which are out of scope for the paper and reserved for a companion study.

---

## What this repository provides

- A **schema audit** of three public financial datasets (one per task),
  documenting that each carries a determination label but no
  judgment-to-provision linkage label.
- Three **illustrative walkthroughs** (advisory, anomaly, accounting),
  each run under three conditions — direct judgment, vanilla RAG, and the
  provision-judgment graph (GraphRAG) — as an existence proof of the
  isomorphic failure and its structural remedy.
- **Figure-generation** code that reproduces the greyscale figures used
  in the paper from the walkthrough outputs.

The three conditions are implemented as deterministic stubs that encode
the traversal logic described in the paper; they are sufficient to
reproduce the reported walkthrough outcomes and figures. Replacing the
stubs with live model calls is left to downstream empirical work.

---

## Repository structure

```text
.
├── data/                           # not tracked; populated by setup (see below)
│   ├── anomaly/raw/                 # transaction CSV
│   ├── advisory/labeled/            # consulting QAQ JSON
│   ├── accounting/labeled/          # accounting QA JSON (standard sub-tree preserved)
│   └── cases/                       # reconstructed, PII-free walkthrough inputs
├── notebooks/
│   ├── setup_data.ipynb             # unpack source archives into data/
│   ├── 00_shared_utils.ipynb        # paths, provision vocabulary, guards, writers
│   ├── 01_advisory_str.ipynb        # audit + walkthrough: suitability vs appropriateness
│   ├── 02_anomaly_str_ctr.ipynb     # audit + walkthrough: STR vs CTR
│   ├── 03_accounting_ifrs15.ipynb   # audit + walkthrough: over-time vs point-in-time
│   └── 04_figures.ipynb             # greyscale figures from walkthrough outputs
└── results/
    ├── figures/                     # generated figures (png + pdf, dpi 600)
    └── tables/                      # schema-audit tables + walkthrough JSON
```

---

## Requirements

- Python 3.10+
- `pandas`, `matplotlib`, `seaborn`

```bash
pip install pandas matplotlib seaborn
```

Notebooks run under Jupyter or any environment that executes `.ipynb`
files. Each analysis notebook is self-contained and can be run
independently; none requires the others to be run first.

---

## Data

This repository does **not** redistribute the source datasets. The study
uses publicly available datasets from a national open-data repository,
under their respective terms of use. In line with those terms, only
newly attached labels and reconstructed, PII-free walkthrough cases
authored for this study are released here; original records are not.

To reproduce the schema audit, obtain the source archives from the
repository and place them alongside `setup_data.ipynb`, then run that
notebook. It unpacks and sorts the files into the `data/` layout the
analysis notebooks expect. The `data/` directory is excluded from version
control (see `.gitignore`).

The three reconstructed walkthrough cases under `data/cases/` are
included in this repository, since they contain no original data.

---

## Reproducing the results

1. **Set up data.** Run `notebooks/setup_data.ipynb` after placing the
   source archives in the expected location. If you run notebooks from
   inside `notebooks/`, set the project root first:
```python
   import os; os.environ["FINGAP_ROOT"] = ".."
```
2. **Run the audits and walkthroughs.** Run `01`, `02`, and `03` in any
   order. Each emits a schema-audit table and a walkthrough JSON to
   `results/tables/`.
3. **Generate figures.** Run `04_figures.ipynb` to produce the greyscale
   figures in `results/figures/` (PNG and PDF, 600 dpi).

Expected outputs:

| Output | Location |
|---|---|
| Schema-audit tables (one per task) | `results/tables/*_schema_audit.csv` |
| Walkthrough results (one per task) | `results/tables/*_walkthrough.json` |
| Traceability matrix figure | `results/figures/fig3a_traceability_matrix.{png,pdf}` |
| Failure-by-condition figure | `results/figures/fig3b_failure_by_condition.{png,pdf}` |

---

## Notes on scope

The evidence here is an **existence proof**, not a distribution. Three
walkthroughs cannot establish that the isomorphism holds at scale; they
show that the framework's objects behave as claimed on realistic
boundary cases. The benchmark whose design the paper publishes
(label schema, labeling protocol, evaluation metrics, and falsification
conditions) is intended to be populated and measured in subsequent
empirical work.

---

## License

Code in this repository is released under the MIT License (see
`LICENSE`). This license covers the code only; the source datasets remain
subject to their own terms of use and are not redistributed here.
