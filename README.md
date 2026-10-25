# Judgment-to-Provision Traceability in Financial LLMs

Replication code and data for a study submitted to a peer-reviewed journal
under **double-anonymous review**. All author and institutional identifiers
are intentionally omitted.

The study reframes regulatory risk in financial large language models (LLMs)
as a failure of **judgment-to-provision traceability** — an LLM can reach the
right determination while being unable to show *which provision grounds it* —
and tests, in a controlled experiment, whether the same failure structure
recurs across three regulatory tasks and whether an explicit
provision-judgment graph repairs it.

| Task | Regulatory boundary | Governing provisions |
|------|--------------------|----------------------|
| **Advisory** | suitability vs. appropriateness | FCPA\* Art. 17 / Art. 18 (+ Art. 19) |
| **Anomaly detection** | STR vs. CTR | TFTIA† Art. 4 / Art. 4-2 (+ Enf. Decree Art. 8-2) |
| **Accounting** | over-time vs. point-in-time | K-IFRS 1115 para. 35 / 35(3) / 38 |

\* **FCPA = (Korean) Financial Consumer Protection Act** — *not* the U.S. Foreign
Corrupt Practices Act. † **TFTIA = Act on Reporting and Using Specified
Financial Transaction Information.**

## What the experiment does

Each case is run under **three conditions that share the same model and the
same case facts**, differing only in the evidence scaffold:

1. **Direct** — model judgment only, no external text.
2. **Vanilla RAG** — top-*k* passages (`k=4`) retrieved from a regulatory
   corpus by cosine similarity over `text-embedding-3-small`, 600-char chunks
   with 100-char overlap.
3. **Provision-Judgment GraphRAG** — a manually-curated graph supplied as
   *general rule structure* (each provision with its triggering condition and
   supersession status); citations are constrained to canonical, non-superseded
   identifiers by a citation guard. The graph encodes the rules, **not** the
   answer to any case, so the model must still perform the subsumption.

The full matrix is **3 conditions × 3 tasks × 3 models × 5 repeats = 2,430
runs**, at temperature 0.7 with a distinct seed per repeat. Grounding is scored
by a rule-based check and, independently, by an LLM judge (held at temperature
0) that never sees the case authors' reasoning.

Reported metrics (empirical, mean ± std over repeats): determination accuracy,
**traceability completion rate**, **correct-but-untraceable rate** (the study's
core quantity), the five-type failure profile, boundary-misjudgment detection,
and a **cross-task failure-profile similarity** (the structural-recurrence /
"isomorphism" metric).

### Headline result (from the notebooks)

| Condition | Det. accuracy | Traceability | Correct-but-untraceable |
|-----------|:---:|:---:|:---:|
| Direct | 54–81% (rises with model size) | **0% at every model size** | high |
| Vanilla RAG | 70–84% | 0–12% | **highest (up to ~77%)** |
| GraphRAG | 89–98% | **68–96%** | low |

Scaling the model closes the *accuracy* gap but not the *traceability* gap;
only the graph recovers traceability, and it removes hallucinated citations
entirely (0% of GraphRAG failures). Rule-based and LLM-judge grounding agree on
96.1% of runs.

## Repository layout

```
.
├── .env.example               # copy to .env (project root) and add your API key
├── requirements.txt
├── data/
│   ├── corpus/<task>.json      # RAG corpus: governing + distractor provisions (shipped)
│   ├── graph/<task>.json       # provision-judgment graph, manually curated (shipped)
│   ├── cases/<task>.json       # case bank: 18/task, expert-adjudicated (shipped)
│   └── cache/                  # LLM response cache (git-ignored)
├── notebooks/
│   ├── fingap_core.py              # shared core: client, RAG, graph, prompts, scorer
│   ├── _build_artifacts.py         # authored corpus/graph/cases (version-controlled)
│   ├── 00_shared_utils.ipynb       # load & smoke-test the core
│   ├── 01_build_corpus_graph_cases.ipynb
│   ├── 02_schema_audit.ipynb       # data-level audit of raw AI-Hub schemas
│   ├── 03_experiment_advisory.ipynb
│   ├── 04_experiment_anomaly.ipynb
│   ├── 05_experiment_accounting.ipynb
│   ├── 06_metrics.ipynb            # aggregate runs -> metrics_*.csv
│   └── 07_figures.ipynb            # greyscale figures, dpi 600, png + pdf
└── results/
    ├── figures/               # generated (git-ignored)
    └── tables/                # generated (git-ignored)
```

Each notebook is a single self-documenting code cell; all comments are in
English. Notebooks `00`–`07` are run in order from the `notebooks/` folder.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env         # then edit .env and add OPENAI_API_KEY
```

`.env` lives in the **project root** (one level above `notebooks/`):

```
OPENAI_API_KEY=sk-...
LLM_MODEL_WEAK=gpt-4o-mini
LLM_MODEL_MID=gpt-5.4-mini
LLM_MODEL_STRONG=gpt-5.4
FINGAP_TEMPERATURE=0.7
FINGAP_REPEATS=5
```

### Mock vs. live

- **Mock (offline, no key, no cost):** if `OPENAI_API_KEY` is absent, or
  `FINGAP_MODE=mock`, the whole pipeline runs with a deterministic surrogate
  LLM and surrogate embeddings, so the build → run → score → figures path can
  be verified end-to-end without network or cost. *Mock outputs are surrogate
  and are not experimental data.*
- **Live:** with a valid key in `.env`, notebooks `03`–`05` call the API.

Repeats at temperature > 0 are genuinely independent draws: `run_index` is
folded into both the response-cache key and the per-call seed, so five repeats
produce five samples (not one cached result), which is what yields the ± std.

## How to run

```bash
cd notebooks
jupyter notebook        # run 00 → 07 in order
```

Headless:

```bash
cd notebooks
for nb in 00_shared_utils 01_build_corpus_graph_cases 02_schema_audit \
          03_experiment_advisory 04_experiment_anomaly 05_experiment_accounting \
          06_metrics 07_figures; do
  jupyter nbconvert --to notebook --execute --inplace "$nb.ipynb" \
    --ExecutePreprocessor.timeout=3600
done
```

Cost scales as `cases × 3 conditions × tiers × repeats` (+ one judge call per
correctly-cited run). For a cheap smoke test set `FINGAP_MAX_CASES=2` and
`FINGAP_TIERS=weak` in `.env`, then scale up.

## Data

The **corpus, provision graph, and case bank** under `data/{corpus,graph,cases}/`
are research-authored, PII-free, and shipped with the repository. The case gold
labels have been **independently adjudicated by a domain expert** (a senior
credit-rating and financial-regulation specialist), who confirmed all 54 cases
with no corrections; each case records `expert_adjudicated`, `adjudicator`, and
the adjudication comment.

The raw **AI-Hub** datasets are **not redistributed** (per their terms of use).
To run the data-level schema audit (`02`), place the labelled trees under
`data/advisory/`, `data/anomaly/`, `data/accounting/`; they are git-ignored.
The experiment notebooks `03`–`05` do **not** require the raw data.

**Windows note:** the schema audit opens deeply-nested Korean file paths; the
notebook uses the `\\?\` extended-length prefix so it works past the 260-char
`MAX_PATH` limit. If you still see unreadable files, move the project to a
shorter path (e.g. `C:\fingap\`).

## Scope and limitations

The experiment is a **controlled study on a reconstructed case bank**, not a
field-scale measurement on the source datasets. Its gold labels were confirmed
by a single independent expert; multi-expert adjudication and field-scale
prevalence measurement are the subject of a companion study. See the manuscript
for the full statement of scope and the benchmark's falsification conditions.
