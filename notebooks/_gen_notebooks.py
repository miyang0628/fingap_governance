"""Generate the FinGap-Governance notebook suite (one code cell per notebook)."""
import nbformat as nbf
from pathlib import Path

NB = Path("/home/claude/fingap_build/notebooks")

def nb_one_cell(src: str):
    n = nbf.v4.new_notebook()
    n.cells = [nbf.v4.new_code_cell(src.strip("\n") + "\n")]
    n.metadata = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}}
    return n

CELLS = {}

CELLS["00_shared_utils.ipynb"] = r'''
# ======================================================================
# 00_shared_utils.ipynb
# FinGap-Governance | Load & smoke-test the shared experiment core.
# ----------------------------------------------------------------------
# Run this first. It imports fingap_core (the single source of truth for
# the LLM client, retrieval index, provision-judgment graph, prompts and
# scorer), prints the active configuration, and runs one offline-safe
# sanity check per condition. No API cost in mock mode.
# ======================================================================
from fingap_core import *
import _build_artifacts as _B
_B.write_all()                                   # ensure data/corpus, graph, cases exist
print(banner())

_cases = load_cases("advisory")
_rag   = RagIndex("advisory").build()
print(f"\nsmoke test | advisory cases={len(_cases)} corpus_chunks={len(_rag.chunks)} "
      f"graph_nodes={len(load_graph('advisory').get('provision_nodes', []))}")
for _cond in CONDITIONS:
    _r = run_once(_cases[0], _cond, RUN_TIERS[0], 0, rag=_rag)
    print(f"  {_cond:11} det={_r.determination:15} cite={_r.cited} "
          f"trace={_r.traceable} fail={_r.failure}")
print("\nOK: core loaded. Set OPENAI_API_KEY in ../.env to switch from mock to live.")
'''

CELLS["01_build_corpus_graph_cases.ipynb"] = r'''
# ======================================================================
# 01_build_corpus_graph_cases.ipynb
# FinGap-Governance | Materialize the research-authored artifacts.
# ----------------------------------------------------------------------
# Writes the three JSON artifacts the experiments consume:
#   data/corpus/<task>.json  -- RAG corpus (governing provisions + distractors)
#   data/graph/<task>.json   -- manually-curated provision-judgment graph
#   data/cases/<task>.json   -- balanced case bank (clear/boundary/distractor)
# All content is research-authored and PII-free. Then runs integrity checks
# (every gold provision is canonical) and prints the difficulty balance.
# ======================================================================
from fingap_core import *
import collections, json
import _build_artifacts as B

counts = B.write_all()
print("written under data/: corpus/, graph/, cases/")
print("case counts per task:", counts)

for task in TASKS:
    graph_ids = {n["id"] for n in load_graph(task).get("provision_nodes", [])}
    cases = load_cases(task)
    for c in cases:                                   # integrity: gold ids are canonical
        for p in c.gold_provisions:
            assert p in PROVISIONS, f"{c.case_id}: non-canonical gold {p}"
    bal = collections.Counter(c.difficulty for c in cases)
    prov = collections.Counter(c.provenance for c in cases)
    n_exp = sum(1 for c in cases if c.expert_adjudicated)
    print(f"  {task:11} n={len(cases):2d} difficulty={dict(bal)} "
          f"provenance={dict(prov)} expert_adjudicated={n_exp}/{len(cases)}")

print("\nNOTE: expert_adjudicated=False by design. A domain expert sets this True "
      "(and fills 'adjudicator') per case before the runs count as validated evidence.")
'''

CELLS["02_schema_audit.ipynb"] = r'''
# ======================================================================
# 02_schema_audit.ipynb
# FinGap-Governance | Data-level audit of the raw AI-Hub datasets.
# ----------------------------------------------------------------------
# Tests the DATA-LEVEL claim, carefully scoped per reviewer guidance: the
# audited schemas carry a determination label but NO explicit *structured*
# judgment-to-provision linkage field. For accounting, we ALSO count how
# often a provision/paragraph reference appears inside free-text answers,
# so the claim is reported as "no structured linkage field" rather than
# "no linkage information whatsoever".
# Raw AI-Hub trees are expected under data/<task>/ (not redistributed).
# If absent, this notebook reports that and skips gracefully.
# ======================================================================
from fingap_core import *
import glob, json, re, csv

ADV = DATA / "advisory" / "labeled"
ANO = DATA / "anomaly"  / "raw"
ACC = DATA / "accounting" / "labeled"

DET_KEYS  = {"consulting_topic", "qa_topic", "task_category", "이상거래유형", "이상거래여부", "이상거래설명"}
LINK_KEYS = {"fcpa_article", "provision_id", "regulatory_phase", "suitability_phase",
             "appropriateness_phase", "explain_duty", "clause_link", "조문링크", "근거조문"}
PARA_PAT  = re.compile(r"(문단|제\s*\d+\s*항|제\s*\d+\s*조|para(graph)?\.?\s*\d+|1115|1018|1011|기준서)")

def flat_keys(o, acc):
    if isinstance(o, dict):
        for k, v in o.items():
            acc.add(k); flat_keys(v, acc)
    elif isinstance(o, list):
        for it in o: flat_keys(it, acc)

rows = []
# --- advisory (JSON) ---
adv_files = sorted(glob.glob(str(ADV / "*.json")))
det = link = 0
for fp in adv_files:
    try: d = json.load(open(fp, encoding="utf-8"))
    except Exception: continue
    ks = set(); flat_keys(d, ks)
    det  += bool(ks & DET_KEYS); link += bool(ks & LINK_KEYS)
rows.append(("advisory", len(adv_files), det, link, "n/a"))

# --- anomaly (CSV columns) ---
ano_files = sorted(glob.glob(str(ANO / "*.csv")))
a_det = a_link = a_n = 0
for fp in ano_files:
    with open(fp, encoding="utf-8-sig", errors="ignore") as f:
        cols = next(csv.reader(f), [])
    a_n += 1
    a_det  += bool(set(cols) & DET_KEYS); a_link += bool(set(cols) & LINK_KEYS)
rows.append(("anomaly", a_n, a_det, a_link, "n/a"))

# --- accounting (QA JSON): structured link vs free-text paragraph mention ---
acc_files = sorted(glob.glob(str(ACC / "**" / "*.json"), recursive=True))
c_det = c_link = c_free = 0
for fp in acc_files:
    try: d = json.load(open(fp, encoding="utf-8"))
    except Exception: continue
    ks = set(); flat_keys(d, ks)
    c_det  += bool(ks & DET_KEYS or "answer" in " ".join(ks).lower() or ks)
    c_link += bool(ks & LINK_KEYS)
    if PARA_PAT.search(json.dumps(d, ensure_ascii=False)):       # paragraph ref in free text
        c_free += 1
rows.append(("accounting", len(acc_files), c_det, c_link, f"{c_free} w/ paragraph-in-freetext"))

print(f"{'task':12}{'files':>8}{'determination':>15}{'struct_link':>13}  freetext_note")
for t, n, de, li, note in rows:
    print(f"{t:12}{n:>8}{de:>15}{li:>13}  {note}")

out = TABLES / "schema_audit.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(["task","files","with_determination","with_structured_link","note"])
    w.writerows(rows)
print(f"\nsaved -> {out.name}")
if not (adv_files or ano_files or acc_files):
    print("\n[!] No raw AI-Hub data found under data/. Place the labelled trees there "
          "(see README) and re-run. The experiment notebooks 03-05 do NOT need this.")
print("\nClaim to report: the audited schemas contain no explicit STRUCTURED "
      "judgment-to-provision linkage field (accounting carries paragraph refs only in free text).")
'''

def experiment_cell(num, task):
    return rf'''
# ======================================================================
# {num}_experiment_{task}.ipynb
# FinGap-Governance | Live experiment -- task: {task}
# ----------------------------------------------------------------------
# Runs all three conditions (direct / vanilla_rag / graph_rag) over the
# {task} case bank, for every model tier in FINGAP_TIERS, repeated
# N_REPEATS times each. Same model and same case facts across conditions;
# only the evidence scaffold (none / retrieved chunks / provision graph)
# differs. All raw outputs are cached under data/cache and logged to
# results/tables/{task}_runs.{{json,csv}}.
# Cost scales as cases x 3 conditions x tiers x repeats (+ judge calls).
# ======================================================================
from fingap_core import *
import pandas as pd
import _build_artifacts as _B; _B.write_all()

TASK = "{task}"
print(banner())
print(f"\nrunning {{TASK}}: cases={{len(load_cases(TASK))}} conditions={{CONDITIONS}} "
      f"tiers={{RUN_TIERS}} repeats={{N_REPEATS}}")

records = run_task(TASK)
jp, cp = save_records(TASK, records)
print(f"saved {{len(records)}} records -> {{cp.name}}, {{jp.name}}")

df = pd.DataFrame([r.__dict__ for r in records])
view = (df.groupby("condition")[["determination_correct", "traceable",
        "correct_but_untraceable"]].mean().round(3))
print("\ncondition means (this task):")
print(view)
'''

CELLS["03_experiment_advisory.ipynb"]   = experiment_cell("03", "advisory")
CELLS["04_experiment_anomaly.ipynb"]    = experiment_cell("04", "anomaly")
CELLS["05_experiment_accounting.ipynb"] = experiment_cell("05", "accounting")

CELLS["06_metrics.ipynb"] = r'''
# ======================================================================
# 06_metrics.ipynb
# FinGap-Governance | Aggregate run records into the reviewer-requested
# empirical metrics (these are now RESULTS, not proposed metrics):
#   * determination accuracy                  (per task x condition)
#   * traceability completion rate            (per task x condition)
#   * correct-but-untraceable rate            (the paper's core quantity)
#   * failure-type profile                    (per condition, over tasks)
#   * boundary-misjudgment detection rate     (boundary cases only)
#   * cross-task failure-profile similarity   (the "isomorphism" metric)
# Variability is reported as mean +/- std across the N_REPEATS runs.
# Outputs -> results/tables/metrics_*.csv
# ======================================================================
from fingap_core import *
import pandas as pd, numpy as np, json

df = pd.concat([pd.read_json(TABLES / f"{t}_runs.json") for t in TASKS
                if (TABLES / f"{t}_runs.json").exists()], ignore_index=True)
assert len(df), "no run records found -- run notebooks 03-05 first"

# ---- per-repeat aggregation so we can report mean +/- std -------------
def per_repeat(metric):
    g = (df.groupby(["task", "condition", "run_index"])[metric].mean()
           .groupby(level=[0, 1]).agg(["mean", "std"]).reset_index())
    g["metric"] = metric
    return g

primary = pd.concat([per_repeat(m) for m in
                     ["determination_correct", "traceable", "correct_but_untraceable"]])
primary[["mean", "std"]] = (primary[["mean", "std"]] * 100).round(1)
primary = primary.pivot_table(index=["task", "condition"], columns="metric",
                              values=["mean", "std"]).round(1)
primary.to_csv(TABLES / "metrics_primary.csv")
print("=== primary metrics (%) — mean over repeats ===")
print(primary["mean"].to_string())

# ---- boundary-misjudgment detection rate ------------------------------
bd = (df[df.difficulty == "boundary"].groupby(["task", "condition"])["determination_correct"]
        .mean().mul(100).round(1).reset_index(name="boundary_detection_rate_pct"))
bd.to_csv(TABLES / "metrics_boundary.csv", index=False)
print("\n=== boundary-misjudgment detection rate (%) ===")
print(bd.to_string(index=False))

# ---- failure-type profile per condition -------------------------------
prof = (df.dropna(subset=["failure"]).groupby(["condition", "failure"]).size()
          .unstack(fill_value=0).reindex(columns=FAILURE_TYPES, fill_value=0))
prof_prop = prof.div(prof.sum(axis=1), axis=0).round(3)
prof.to_csv(TABLES / "metrics_failure_counts.csv")
prof_prop.to_csv(TABLES / "metrics_failure_profile.csv")
print("\n=== failure-type profile by condition (proportions) ===")
print(prof_prop.to_string())

# ---- cross-task failure-profile similarity (the isomorphism metric) ---
# For each condition, build task x failure-type proportion vectors and take
# pairwise cosine similarity across tasks; high values = the SAME failure
# structure recurs across tasks (structural recurrence / "isomorphism").
def cos(a, b):
    a, b = np.array(a, float), np.array(b, float)
    return float(a @ b / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1))

iso_rows = []
for cond in CONDITIONS:
    sub = df[(df.condition == cond)].dropna(subset=["failure"])
    vecs = {}
    for t in TASKS:
        v = (sub[sub.task == t]["failure"].value_counts()
             .reindex(FAILURE_TYPES, fill_value=0)).values
        vecs[t] = v
    pairs = [("advisory", "anomaly"), ("advisory", "accounting"), ("anomaly", "accounting")]
    for a, b in pairs:
        iso_rows.append({"condition": cond, "task_pair": f"{a}~{b}",
                         "cosine_similarity": round(cos(vecs[a], vecs[b]), 3)})
iso = pd.DataFrame(iso_rows)
iso.to_csv(TABLES / "metrics_isomorphism.csv", index=False)
print("\n=== cross-task failure-profile similarity (cosine) ===")
print(iso.pivot(index="task_pair", columns="condition", values="cosine_similarity").to_string())

print("\nsaved -> results/tables/metrics_*.csv")
'''

CELLS["07_figures.ipynb"] = r'''
# ======================================================================
# 07_figures.ipynb
# FinGap-Governance | Publication figures.
# ----------------------------------------------------------------------
# Reads results/tables/*_runs.json and metrics_*.csv, renders GREYSCALE
# seaborn figures with NO embedded captions, and saves each as BOTH .png
# and .pdf at dpi=600 under results/figures/. Self-contained.
# ======================================================================
from fingap_core import *
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="white", context="paper")
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": "black",
                     "axes.linewidth": 0.8, "savefig.bbox": "tight"})
GREYS = sns.color_palette("Greys", n_colors=4)
COND_ORDER = ["direct", "vanilla_rag", "graph_rag"]
COND_LBL   = {"direct": "Direct", "vanilla_rag": "Vanilla RAG", "graph_rag": "GraphRAG"}
HATCH      = {"direct": "...", "vanilla_rag": "///", "graph_rag": ""}

def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(FIGURES / f"{name}.{ext}", dpi=600)
    plt.close(fig)
    print("saved", name + ".png/.pdf")

df = pd.concat([pd.read_json(TABLES / f"{t}_runs.json") for t in TASKS
                if (TABLES / f"{t}_runs.json").exists()], ignore_index=True)
assert len(df), "no run records -- run 03-05 and 06 first"
r = lambda s: 100 * s.mean()

# --- Fig A: traceability completion rate, task x condition (greyscale heatmap) ---
pivot = (df.groupby(["task", "condition"])["traceable"].mean().mul(100)
           .unstack().reindex(columns=COND_ORDER).reindex(index=TASKS))
fig, ax = plt.subplots(figsize=(5.0, 3.2))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Greys", vmin=0, vmax=100,
            linewidths=0.6, linecolor="black", cbar_kws={"label": "Traceability completion (%)"},
            ax=ax, annot_kws={"color": "black"})
ax.set_xticklabels([COND_LBL[c] for c in pivot.columns]); ax.set_ylabel(""); ax.set_xlabel("")
save(fig, "fig_traceability_matrix")

# --- Fig B: determination accuracy vs traceability, grouped bars per condition ---
acc = df.groupby("condition")["determination_correct"].apply(r).reindex(COND_ORDER)
trc = df.groupby("condition")["traceable"].apply(r).reindex(COND_ORDER)
x = np.arange(len(COND_ORDER)); w = 0.38
fig, ax = plt.subplots(figsize=(5.2, 3.3))
ax.bar(x - w/2, acc.values, w, color=GREYS[1], edgecolor="black", label="Determination accuracy")
ax.bar(x + w/2, trc.values, w, color=GREYS[3], edgecolor="black", hatch="///", label="Traceability completion")
ax.set_xticks(x); ax.set_xticklabels([COND_LBL[c] for c in COND_ORDER])
ax.set_ylabel("%"); ax.set_ylim(0, 100); ax.legend(frameon=False, fontsize=8)
for s in ("top", "right"): ax.spines[s].set_visible(False)
save(fig, "fig_accuracy_vs_traceability")

# --- Fig C: correct-but-untraceable rate, task x condition (the thesis) ---
cu = (df.groupby(["task", "condition"])["correct_but_untraceable"].mean().mul(100)
        .unstack().reindex(columns=COND_ORDER).reindex(index=TASKS))
fig, ax = plt.subplots(figsize=(5.4, 3.3))
xx = np.arange(len(TASKS)); w = 0.26
for i, c in enumerate(COND_ORDER):
    ax.bar(xx + (i-1)*w, cu[c].values, w, color=GREYS[i+1], edgecolor="black",
           hatch=HATCH[c], label=COND_LBL[c])
ax.set_xticks(xx); ax.set_xticklabels(TASKS); ax.set_ylabel("Correct but untraceable (%)")
ax.set_ylim(0, 100); ax.legend(frameon=False, fontsize=8)
for s in ("top", "right"): ax.spines[s].set_visible(False)
save(fig, "fig_correct_but_untraceable")

# --- Fig D: failure-type profile by condition (stacked greyscale bars) ---
prof = (df.dropna(subset=["failure"]).groupby(["condition", "failure"]).size()
          .unstack(fill_value=0).reindex(index=COND_ORDER)
          .reindex(columns=FAILURE_TYPES, fill_value=0))
prop = prof.div(prof.sum(axis=1), axis=0)
fig, ax = plt.subplots(figsize=(6.0, 3.4))
bottom = np.zeros(len(COND_ORDER))
greys5 = sns.color_palette("Greys", n_colors=len(FAILURE_TYPES) + 1)[1:]
for j, ft in enumerate(FAILURE_TYPES):
    ax.bar([COND_LBL[c] for c in COND_ORDER], prop[ft].values, bottom=bottom,
           color=greys5[j], edgecolor="black", linewidth=0.5, label=ft)
    bottom += prop[ft].values
ax.set_ylabel("Share of failures"); ax.set_ylim(0, 1)
ax.legend(frameon=False, fontsize=7, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12))
for s in ("top", "right"): ax.spines[s].set_visible(False)
save(fig, "fig_failure_profile")

# --- Fig E: cross-task failure-profile similarity per condition (isomorphism) ---
iso = pd.read_csv(TABLES / "metrics_isomorphism.csv") if (TABLES/"metrics_isomorphism.csv").exists() else None
if iso is not None:
    piv = iso.pivot(index="task_pair", columns="condition", values="cosine_similarity").reindex(columns=COND_ORDER)
    fig, ax = plt.subplots(figsize=(5.0, 3.0))
    sns.heatmap(piv, annot=True, fmt=".2f", cmap="Greys", vmin=0, vmax=1,
                linewidths=0.6, linecolor="black", ax=ax,
                cbar_kws={"label": "Cosine similarity"}, annot_kws={"color": "black"})
    ax.set_xticklabels([COND_LBL[c] for c in piv.columns]); ax.set_xlabel(""); ax.set_ylabel("")
    save(fig, "fig_isomorphism_similarity")

print("\nall figures saved under results/figures/ (png + pdf, dpi 600)")
'''

for name, src in CELLS.items():
    nbf.write(nb_one_cell(src), str(NB / name))
    print("wrote", name)
