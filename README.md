
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
