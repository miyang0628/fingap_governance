# `data/` — datasets and research-authored artifacts

This folder holds everything the experiment reads. The research-authored,
PII-free artifacts (`corpus/`, `graph/`, `cases/`) are shipped with the
repository; the raw AI-Hub datasets are **not** redistributed (see below).

```
data/
├── corpus/<task>.json   RAG corpus: governing + distractor provisions
├── graph/<task>.json    provision-judgment graph (manually curated)
├── cases/<task>.json    case bank: 18 cases/task, expert-adjudicated
├── cache/               LLM response cache (generated; git-ignored)
└── (advisory|anomaly|accounting)/   raw AI-Hub trees — NOT in this repo
```

`<task>` is one of `advisory`, `anomaly`, `accounting`.

## `corpus/<task>.json`

A list of provision documents used by the **Vanilla RAG** condition. Each
entry is `{provision_id, label, text}`. The corpus contains both the
governing provisions and distractor provisions, so retrieval is
non-trivial (a relevant-looking passage is not necessarily the grounding
provision). Texts are plain-language summaries authored by the research
team; replace them with full licensed statutory text locally if required.

## `graph/<task>.json`

The manually-curated **provision-judgment graph** supplied to the
GraphRAG condition. Fields:

- `provision_nodes`: `{id, label, status}` — `status` is `current` or `superseded`.
- `judgment_edges`: `{condition, determination, provision_id, priority}` —
  the *general* triggering condition for each determination (not the answer
  to any specific case).
- `supersession_edges`: `{old, new}` — superseded provisions are blocked
  from being cited as current by the citation guard.

The graph encodes rule structure only; the model must still perform the
subsumption from case facts.

## `cases/<task>.json`

The case bank evaluated in the controlled experiment: 18 PII-free,
research-authored cases per task (54 total), balanced across
`clear` / `boundary` / `distractor` difficulty strata. Per-case fields:

| field | meaning |
|-------|---------|
| `case_id` | e.g. `ADV-01` |
| `task` | advisory / anomaly / accounting |
| `boundary_axis` | the normative boundary at issue |
| `facts` | PII-free narrative shown to the model |
| `gold_determination` | from the closed label set for the task |
| `gold_provisions` | canonical provision id(s) that must ground the determination |
| `discriminating_condition` | the single fact that flips the boundary |
| `difficulty` | `clear` \| `boundary` \| `distractor` |
| `provenance` | `research_authored` |
| `expert_adjudicated` | `true` once a domain expert has signed off |
| `adjudicator` | role-level description of the adjudicator (anonymized) |
| `adjudication` | `{determination_ok, provision_ok, boundary_ok, comment}` |
| `notes` | author notes plus the expert's rationale |

**Adjudication status.** All 54 gold labels were independently adjudicated
by a domain expert (a senior credit-rating and financial-regulation
specialist) who confirmed every determination and governing provision with
no corrections. The adjudication is recorded per case in the fields above.

## Raw AI-Hub datasets (not included)

The schema audit (`notebooks/02_schema_audit.ipynb`) reads the original
AI-Hub labelled datasets. These are **not redistributed** here, in keeping
with their terms of use. To run the audit, place the labelled trees under:

```
data/advisory/labeled/      (call-centre consulting QA, JSON)
data/anomaly/raw/           (transaction CSV)
data/accounting/labeled/    (standards QA, JSON; 대분류/중분류 subtree preserved)
```

These paths are git-ignored. The experiment notebooks (`03`–`05`) do **not**
require the raw data — they run entirely on `cases/`, `corpus/`, and `graph/`.
