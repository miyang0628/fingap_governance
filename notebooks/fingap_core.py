# ======================================================================
# fingap_core.py
# FinGap-Governance | Shared experiment core (imported by notebooks 00-06)
# ----------------------------------------------------------------------
# Single source of truth for the empirical pipeline. Every notebook does
# `from fingap_core import *`, so the LLM client, the retrieval index,
# the provision-judgment graph, the prompts, and the scorer are byte-for-
# byte IDENTICAL across the three conditions and three tasks. This is a
# deliberate design response to the review requirement that the baselines
# and the proposed method be given comparable information and be assessed
# by the same instruments.
#
# Modes:
#   * live  : calls the OpenAI API using keys/models from ../.env
#   * mock  : fully offline; deterministic surrogate LLM + embeddings so
#             the whole pipeline (build -> run -> score -> figures) can be
#             verified without network or cost. Mock outputs are NOT data.
# Mode is auto-detected: live if OPENAI_API_KEY is present and
# FINGAP_MODE != "mock"; otherwise mock.
# ======================================================================

from __future__ import annotations
import os, re, json, glob, csv, time, hashlib, random
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Any

# ---- 1. Paths & environment ------------------------------------------
# Notebooks run from notebooks/; the project ROOT is its parent, which is
# where .env lives ("just above the notebooks folder", per the setup).
def _discover_root() -> Path:
    env = os.environ.get("FINGAP_ROOT")
    if env:
        return Path(env).resolve()
    here = Path.cwd().resolve()
    for cand in (here, *here.parents):
        if (cand / ".env").exists() or (cand / "data").is_dir():
            # prefer a dir that has data/ as a child (the project root)
            if (cand / "data").is_dir() or (cand / "notebooks").is_dir():
                return cand
    # fallback: parent of notebooks/, else cwd
    return here.parent if here.name == "notebooks" else here

ROOT       = _discover_root()
DATA       = ROOT / "data"
RAW        = DATA                      # raw AI-Hub trees live under data/<task>/...
CORPUS_DIR = DATA / "corpus"
GRAPH_DIR  = DATA / "graph"
CASES_DIR  = DATA / "cases"
CACHE_DIR  = DATA / "cache"
RESULTS    = ROOT / "results"
FIGURES    = RESULTS / "figures"
TABLES     = RESULTS / "tables"
for _p in (CORPUS_DIR, GRAPH_DIR, CASES_DIR, CACHE_DIR, FIGURES, TABLES):
    _p.mkdir(parents=True, exist_ok=True)

# Load .env from ROOT (python-dotenv if available; otherwise a tiny parser)
def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(path, override=False)
        return
    except Exception:
        pass
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_dotenv(ROOT / ".env")

# ---- 2. Configuration -------------------------------------------------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

MODELS = {
    "weak":   os.environ.get("LLM_MODEL_WEAK",   "gpt-4o-mini"),
    "mid":    os.environ.get("LLM_MODEL_MID",    "gpt-5.4-mini"),
    "strong": os.environ.get("LLM_MODEL_STRONG", "gpt-5.4"),
}
# Model tiers actually exercised in the main run (comma-separated env override).
RUN_TIERS   = [t.strip() for t in os.environ.get("FINGAP_TIERS", "weak,mid,strong").split(",") if t.strip()]
# Model used as the independent LLM-judge for grounding (separate instrument).
JUDGE_TIER  = os.environ.get("FINGAP_JUDGE_TIER", "strong")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")

N_REPEATS   = int(os.environ.get("FINGAP_REPEATS", "3"))      # repeated runs per (case,condition,model)
TEMPERATURE = float(os.environ.get("FINGAP_TEMPERATURE", "0.0"))
SEED        = int(os.environ.get("FINGAP_SEED", "20260101"))
TOP_K       = int(os.environ.get("FINGAP_TOPK", "4"))          # chunks retrieved in vanilla RAG
CHUNK_CHARS = int(os.environ.get("FINGAP_CHUNK_CHARS", "600")) # RAG chunk size (chars)
CHUNK_OVER  = int(os.environ.get("FINGAP_CHUNK_OVERLAP", "100"))
MAX_CASES   = int(os.environ.get("FINGAP_MAX_CASES", "0"))     # 0 = all; else cap per task (smoke tests)
USE_LLM_JUDGE = os.environ.get("FINGAP_LLM_JUDGE", "1") == "1"

_forced_mock = os.environ.get("FINGAP_MODE", "").lower() == "mock"
MODE = "live" if (OPENAI_API_KEY and not _forced_mock) else "mock"

CONDITIONS = ["direct", "vanilla_rag", "graph_rag"]
TASKS      = ["advisory", "anomaly", "accounting"]

# ---- 3. Canonical provision vocabulary & determination labels ---------
# Canonical identifiers are the ONLY citations the graph condition may
# emit; anything outside this set (or a superseded id) is a hallucination.
PROVISIONS: dict[str, dict] = {
    # --- advisory: Korean Financial Consumer Protection Act (FCPA == 금융소비자보호법) ---
    "FCPA-Art17":  {"task": "advisory",  "label": "FCPA Art. 17 (suitability)",               "status": "current"},
    "FCPA-Art18":  {"task": "advisory",  "label": "FCPA Art. 18 (appropriateness)",           "status": "current"},
    "FCPA-Art19":  {"task": "advisory",  "label": "FCPA Art. 19 (duty to explain)",           "status": "current"},
    "FCPA-Art20":  {"task": "advisory",  "label": "FCPA Art. 20 (unfair business conduct)",   "status": "current"},
    "FCPA-Art21":  {"task": "advisory",  "label": "FCPA Art. 21 (improper solicitation)",     "status": "current"},
    "FCPA-Art22":  {"task": "advisory",  "label": "FCPA Art. 22 (advertising regulation)",    "status": "current"},
    # --- anomaly: TFTIA (특정 금융거래정보의 보고 및 이용 등에 관한 법률) ---
    "TFTIA-Art4":       {"task": "anomaly", "label": "TFTIA Art. 4 (Suspicious Transaction Report)",          "status": "current"},
    "TFTIA-Art4-2":     {"task": "anomaly", "label": "TFTIA Art. 4-2 (Currency Transaction Report)",          "status": "current"},
    "TFTIA-Enf-Art8-2": {"task": "anomaly", "label": "TFTIA Enf. Decree Art. 8-2 (KRW 10M / 1 business day)", "status": "current"},
    "TFTIA-Art2-4":     {"task": "anomaly", "label": "TFTIA Art. 2(4) (definition of money laundering)",      "status": "current"},
    # --- accounting: K-IFRS ---
    "KIFRS1115-P35":   {"task": "accounting", "label": "K-IFRS 1115 para. 35 (satisfied over time)",              "status": "current"},
    "KIFRS1115-P35-3": {"task": "accounting", "label": "K-IFRS 1115 para. 35(3) (no alt. use + enforceable right)", "status": "current"},
    "KIFRS1115-P38":   {"task": "accounting", "label": "K-IFRS 1115 para. 38 (satisfied at a point in time)",      "status": "current"},
    "KIFRS1018":       {"task": "accounting", "label": "K-IFRS 1018 (superseded by 1115)",                        "status": "superseded"},
    "KIFRS1011":       {"task": "accounting", "label": "K-IFRS 1011 (construction contracts, superseded)",        "status": "superseded"},
}
SUPERSEDED = {pid for pid, p in PROVISIONS.items() if p["status"] == "superseded"}

def task_provisions(task: str) -> dict[str, dict]:
    return {k: v for k, v in PROVISIONS.items() if v["task"] == task}

DET_LABELS = {
    "advisory":   ["suitability", "appropriateness", "explain_duty", "none"],
    "anomaly":    ["STR", "CTR", "both", "none"],
    "accounting": ["over_time", "point_in_time", "none"],
}

# The five-type blind-spot taxonomy (paper §4).
FAILURE_TYPES = [
    "boundary_misjudgment",   # wrong side of the discriminating boundary
    "provision_omission",     # determination made with no provision cited
    "misattribution",         # cited a real provision, but the wrong one
    "logic_disconnection",    # right provision cited, but it does not ground the determination
    "hallucination",          # cited a non-canonical or superseded provision as current
]

# ---- 4. Data structures ----------------------------------------------
@dataclass
class Case:
    case_id: str
    task: str
    boundary_axis: str
    facts: str                       # PII-free narrative shown to the model
    gold_determination: str          # from DET_LABELS[task]
    gold_provisions: list            # canonical ids
    discriminating_condition: str    # the single fact that flips the boundary
    difficulty: str                  # "clear" | "boundary" | "distractor"
    provenance: str                  # "research_authored" | "derived_from_aihub"
    expert_adjudicated: bool = False # set True once a domain expert signs off
    adjudicator: str = ""            # anonymized id, filled by the author
    notes: str = ""

@dataclass
class Verdict:
    determination: str = "none"
    cited: list = field(default_factory=list)
    justification: str = ""
    raw: str = ""

@dataclass
class RunRecord:
    case_id: str; task: str; condition: str; model_tier: str; model_name: str
    run_index: int
    gold_determination: str
    gold_provisions: list
    determination: str
    cited: list
    justification: str
    determination_correct: bool
    cited_gold: bool                 # at least one gold provision cited
    grounded_rule: bool              # rule-based grounding (det + gold cite + condition mentioned)
    grounded_judge: Optional[bool]   # independent LLM-judge grounding (None if not run)
    traceable: bool                  # final: determination_correct AND grounded
    correct_but_untraceable: bool    # determination_correct AND NOT traceable  (the paper's thesis)
    failure: Optional[str]           # one of FAILURE_TYPES, or None
    difficulty: str
    provenance: str
    latency_s: float = 0.0

# ---- 5. LLM client (live + mock), with on-disk response cache ---------
_client = None
def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

def _cache_path(key: str) -> Path:
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:40]
    return CACHE_DIR / f"resp_{h}.json"

def _mock_verdict_json(task: str, condition: str, user: str, run_index: int = 0) -> str:
    # Deterministic surrogate that depends on the case facts embedded in the
    # prompt, so mock runs produce varied, condition-dependent behaviour good
    # enough to validate scoring/figures. run_index perturbs the draw so that
    # repeats vary (mirroring temperature>0). These outputs are NOT data.
    seed = int(hashlib.sha256((task + condition + user + f"|r{run_index}").encode()).hexdigest(), 16)
    rnd = random.Random(seed)
    tp = task_provisions(task)
    gold_hint = re.search(r"\[MOCK_GOLD det=(.*?) prov=(.*?) cond=(.*?)\]", user)
    det, prov, cond_txt = ("none", [], "")
    if gold_hint:
        det = gold_hint.group(1)
        prov = [p for p in gold_hint.group(2).split("|") if p]
        cond_txt = gold_hint.group(3)
    # Condition-dependent reliability (mock only): direct < vanilla < graph.
    p_correct = {"direct": 0.45, "vanilla_rag": 0.6, "graph_rag": 0.9}[condition]
    p_ground  = {"direct": 0.2,  "vanilla_rag": 0.4, "graph_rag": 0.88}[condition]
    out_det = det if rnd.random() < p_correct else rnd.choice(DET_LABELS[task])
    if rnd.random() < p_ground and prov:
        out_cite = prov
        just = (f"Because {cond_txt}, {prov[0]} governs the determination."
                if cond_txt else f"The discriminating condition is met, so {prov[0]} governs.")
    else:
        pool = list(tp.keys())
        if condition == "direct" and rnd.random() < 0.5:
            out_cite = []                                  # provision omission
            just = "Based on general principles."
        elif rnd.random() < 0.15:
            out_cite = ["NON-CANONICAL-" + str(rnd.randint(1, 99))]  # hallucination
            just = "Per the applicable rule."
        else:
            out_cite = [rnd.choice(pool)]                  # misattribution / disconnection
            just = "The retrieved provision appears relevant."
    return json.dumps({"determination": out_det, "cited_provisions": out_cite,
                       "justification": just}, ensure_ascii=False)

def call_llm(model: str, system: str, user: str, *, task: str = "", condition: str = "",
             run_index: int = 0, temperature: float = TEMPERATURE, as_json: bool = True,
             use_cache: bool = True) -> tuple[str, float]:
    """Return (content, latency_s). Mock mode never touches the network.
    run_index is folded into BOTH the cache key and the per-call seed so that
    repeated runs at temperature > 0 are genuinely distinct draws (otherwise
    every repeat collapses to one cached response and std is always 0)."""
    seed = SEED + run_index
    cache_key = f"{MODE}|{model}|{temperature}|{seed}|r{run_index}|{system}\n---\n{user}"
    cp = _cache_path(cache_key)
    if use_cache and cp.exists():
        obj = json.loads(cp.read_text(encoding="utf-8"))
        return obj["content"], obj.get("latency_s", 0.0)

    t0 = time.time()
    if MODE == "mock":
        content = _mock_verdict_json(task, condition, user, run_index)
    else:
        client = _get_client()
        # Defensive: some model families reject temperature/seed/json params.
        base = dict(model=model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}])
        attempts = []
        kw = dict(base)
        if as_json: kw["response_format"] = {"type": "json_object"}
        kw["temperature"] = temperature; kw["seed"] = seed
        attempts.append(kw)
        attempts.append({**base, **({"response_format": {"type": "json_object"}} if as_json else {})})
        attempts.append(base)
        content, last_err = None, None
        for kw in attempts:
            try:
                resp = client.chat.completions.create(**kw)
                content = resp.choices[0].message.content
                break
            except Exception as e:                      # noqa: BLE001
                last_err = e; continue
        if content is None:
            raise RuntimeError(f"LLM call failed for {model}: {last_err}")
    latency = time.time() - t0
    if use_cache:
        cp.write_text(json.dumps({"content": content, "latency_s": latency},
                                 ensure_ascii=False), encoding="utf-8")
    return content, latency

# ---- 6. Embeddings + vanilla-RAG retriever ----------------------------
def _mock_embed(text: str, dim: int = 256) -> list[float]:
    rnd = random.Random(int(hashlib.sha256(text.encode()).hexdigest(), 16))
    v = [rnd.gauss(0, 1) for _ in range(dim)]
    n = sum(x * x for x in v) ** 0.5 or 1.0
    return [x / n for x in v]

def embed_texts(texts: list[str]) -> list[list[float]]:
    if MODE == "mock":
        return [_mock_embed(t) for t in texts]
    client = _get_client()
    out, B = [], 64
    for i in range(0, len(texts), B):
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts[i:i + B])
        out.extend([d.embedding for d in resp.data])
    return out

def _cosine(a: list[float], b: list[float]) -> float:
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0

def chunk_text(text: str, size: int = CHUNK_CHARS, overlap: int = CHUNK_OVER) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= size:
        return [text]
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i + size]); i += size - overlap
    return chunks

class RagIndex:
    """Flat cosine-similarity index over corpus chunks (reported mechanism)."""
    def __init__(self, task: str):
        self.task = task
        self.chunks: list[dict] = []
        self.vecs: list[list[float]] = []

    def build(self):
        docs = load_corpus(self.task)              # includes distractor provisions
        texts = []
        for d in docs:
            for j, ch in enumerate(chunk_text(d["text"])):
                self.chunks.append({"provision_id": d["provision_id"],
                                    "label": d["label"], "chunk_id": f'{d["provision_id"]}#{j}',
                                    "text": ch})
                texts.append(ch)
        self.vecs = embed_texts(texts)
        return self

    def retrieve(self, query: str, k: int = TOP_K) -> list[dict]:
        qv = embed_texts([query])[0]
        scored = sorted(((_cosine(qv, v), c) for v, c in zip(self.vecs, self.chunks)),
                        key=lambda x: x[0], reverse=True)
        return [{**c, "score": round(s, 4)} for s, c in scored[:k]]

# ---- 7. Corpus & provision-judgment graph loaders ---------------------
def load_corpus(task: str) -> list[dict]:
    fp = CORPUS_DIR / f"{task}.json"
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else []

def load_graph(task: str) -> dict:
    fp = GRAPH_DIR / f"{task}.json"
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else {}

def format_graph_for_prompt(task: str) -> str:
    """Render the manually-curated provision-judgment graph as the rule
    structure the model must APPLY. It encodes general trigger conditions,
    not the answer to any specific case (this is what breaks the
    'confirmation by construction' circularity flagged in review)."""
    g = load_graph(task)
    lines = []
    for node in g.get("provision_nodes", []):
        tag = " [SUPERSEDED — do not cite as current]" if node.get("status") == "superseded" else ""
        lines.append(f'- {node["id"]} = {node["label"]}{tag}')
    lines.append("")
    lines.append("Judgment rules (provision <- triggering condition):")
    for e in g.get("judgment_edges", []):
        lines.append(f'  * IF {e["condition"]} THEN determination="{e["determination"]}" '
                     f'governed by {e["provision_id"]} (priority {e.get("priority", 0)})')
    if g.get("supersession_edges"):
        lines.append("")
        lines.append("Supersession:")
        for s in g["supersession_edges"]:
            lines.append(f'  * {s["old"]} superseded by {s["new"]} — cite {s["new"]}, never {s["old"]}')
    return "\n".join(lines)

# ---- 8. Prompts for the three conditions ------------------------------
_SYSTEM = ("You are a financial regulatory compliance assistant for the Republic of Korea. "
           "Decide the regulatory determination for the case and cite the governing provision(s). "
           "Respond ONLY with a JSON object: "
           '{"determination": <one label>, "cited_provisions": [<provision ids>], '
           '"justification": <one or two sentences>}. '
           "Do not invent provision identifiers.")

def _det_menu(task: str) -> str:
    return f'Allowed determination labels for this task: {DET_LABELS[task]}.'

def _mock_tag(case: Case) -> str:
    # Only used so the offline mock can imitate a plausible model; the tag is
    # appended in mock mode ONLY and never sent in live mode.
    return (f'\n[MOCK_GOLD det={case.gold_determination} prov={"|".join(case.gold_provisions)} '
            f'cond={case.discriminating_condition}]') if MODE == "mock" else ""

def build_prompt(case: Case, condition: str, rag: Optional[RagIndex] = None) -> str:
    head = f"TASK: {case.task}\n{_det_menu(case.task)}\nCASE FACTS:\n{case.facts}\n"
    if condition == "direct":
        body = ("Use only your own knowledge; no external text is provided. "
                "State the determination and cite the governing provision id(s).")
    elif condition == "vanilla_rag":
        hits = rag.retrieve(case.facts, k=TOP_K) if rag else []
        ctx = "\n\n".join(f'[{h["chunk_id"]}] {h["text"]}' for h in hits)
        body = ("Retrieved regulatory text (top-k by similarity):\n"
                f"{ctx}\n\nUsing the retrieved text, state the determination and cite "
                "the governing provision id(s).")
    elif condition == "graph_rag":
        body = ("Provision-judgment graph (apply the rules to the facts yourself; "
                "cite ONLY ids that appear below and never a superseded id):\n"
                f"{format_graph_for_prompt(case.task)}\n\n"
                "Identify which triggering condition the facts satisfy, give the "
                "determination it implies, and cite the governing provision id.")
    else:
        raise ValueError(condition)
    return head + "\n" + body + _mock_tag(case)

# ---- 9. Output parsing & citation guard -------------------------------
def parse_verdict(raw: str) -> Verdict:
    v = Verdict(raw=raw)
    try:
        m = re.search(r"\{.*\}", raw, re.S)
        obj = json.loads(m.group(0) if m else raw)
        v.determination = str(obj.get("determination", "none")).strip()
        cited = obj.get("cited_provisions", []) or []
        if isinstance(cited, str): cited = [cited]
        v.cited = [str(c).strip() for c in cited]
        v.justification = str(obj.get("justification", "")).strip()
    except Exception:
        v.determination = "none"
    return v

def citation_guard(cited: list) -> list:
    """Applied in the graph condition only: keep canonical, non-superseded ids."""
    return [c for c in cited if c in PROVISIONS and c not in SUPERSEDED]

# ---- 10. Scoring ------------------------------------------------------
def _norm_det(task: str, det: str) -> str:
    d = det.lower().strip()
    table = {
        "advisory":   {"suitability": "suitability", "art17": "suitability", "17": "suitability",
                       "appropriateness": "appropriateness", "art18": "appropriateness", "18": "appropriateness",
                       "explain_duty": "explain_duty", "explain": "explain_duty", "art19": "explain_duty"},
        "anomaly":    {"str": "STR", "ctr": "CTR", "both": "both", "none": "none"},
        "accounting": {"over_time": "over_time", "overtime": "over_time", "over time": "over_time",
                       "point_in_time": "point_in_time", "point in time": "point_in_time",
                       "pointintime": "point_in_time"},
    }.get(task, {})
    for key, val in table.items():
        if key in d:
            return val
    return det if det in DET_LABELS.get(task, []) else "none"

def classify(case: Case, v: Verdict, condition: str) -> dict:
    cited = citation_guard(v.cited) if condition == "graph_rag" else v.cited
    det = _norm_det(case.task, v.determination)
    det_ok = (det == case.gold_determination)
    canonical_cited = [c for c in cited if c in PROVISIONS]
    noncanonical   = [c for c in cited if c not in PROVISIONS]
    superseded_cited = [c for c in cited if c in SUPERSEDED]
    cited_gold = any(c in case.gold_provisions for c in cited)
    cond_hit = _condition_mentioned(case, v.justification)
    grounded_rule = bool(det_ok and cited_gold and cond_hit)

    # Failure typing (priority order mirrors the taxonomy definitions).
    failure = None
    if not grounded_rule:
        if noncanonical or superseded_cited:
            failure = "hallucination"
        elif not cited:
            failure = "provision_omission"
        elif not det_ok:
            failure = "boundary_misjudgment" if case.difficulty == "boundary" else "misattribution"
        elif not cited_gold:
            failure = "misattribution"
        else:  # correct det + gold cited but condition not used to ground it
            failure = "logic_disconnection"
    return {"cited": cited, "determination": det, "determination_correct": det_ok,
            "cited_gold": cited_gold, "grounded_rule": grounded_rule, "failure": failure}

def _condition_mentioned(case: Case, justification: str) -> bool:
    j = justification.lower()
    kws = [w for w in re.split(r"[^a-z0-9]+", case.discriminating_condition.lower()) if len(w) > 3]
    if not kws:
        return bool(j)
    return sum(1 for w in kws if w in j) >= max(1, len(kws) // 3)

_JUDGE_SYSTEM = ("You are an independent reviewer. You are given a case, a determination, a cited "
                 "provision, and a justification. Answer ONLY JSON "
                 '{"grounded": true|false} where grounded means the justification actually uses the '
                 "cited provision and the discriminating fact to support the determination "
                 "(mere mention or recitation is NOT grounding).")

def llm_judge_grounded(case: Case, v: Verdict) -> Optional[bool]:
    if not USE_LLM_JUDGE:
        return None
    user = (f"CASE FACTS: {case.facts}\nDISCRIMINATING FACT: {case.discriminating_condition}\n"
            f"DETERMINATION: {v.determination}\nCITED: {v.cited}\nJUSTIFICATION: {v.justification}")
    if MODE == "mock":
        # surrogate: agree with rule-based grounding most of the time
        seed = int(hashlib.sha256((case.case_id + v.justification).encode()).hexdigest(), 16)
        return random.Random(seed).random() < 0.8
    # The judge is kept deterministic (temperature 0) regardless of the
    # generation temperature, so grounding adjudication is stable.
    content, _ = call_llm(MODELS[JUDGE_TIER], _JUDGE_SYSTEM, user, as_json=True, temperature=0.0)
    try:
        return bool(json.loads(re.search(r"\{.*\}", content, re.S).group(0)).get("grounded", False))
    except Exception:
        return None

# ---- 11. One run ------------------------------------------------------
def run_once(case: Case, condition: str, tier: str, run_index: int,
             rag: Optional[RagIndex] = None) -> RunRecord:
    model = MODELS[tier]
    prompt = build_prompt(case, condition, rag=rag)
    content, latency = call_llm(model, _SYSTEM, prompt, task=case.task,
                                condition=condition, run_index=run_index)
    v = parse_verdict(content)
    c = classify(case, v, condition)
    judge = llm_judge_grounded(case, v) if c["determination_correct"] and c["cited_gold"] else (
        False if not c["grounded_rule"] else None)
    grounded = c["grounded_rule"] if judge is None else (c["grounded_rule"] and judge)
    traceable = bool(c["determination_correct"] and grounded)
    return RunRecord(
        case_id=case.case_id, task=case.task, condition=condition, model_tier=tier,
        model_name=model, run_index=run_index,
        gold_determination=case.gold_determination, gold_provisions=case.gold_provisions,
        determination=c["determination"], cited=c["cited"], justification=v.justification,
        determination_correct=c["determination_correct"], cited_gold=c["cited_gold"],
        grounded_rule=c["grounded_rule"], grounded_judge=judge, traceable=traceable,
        correct_but_untraceable=bool(c["determination_correct"] and not traceable),
        failure=c["failure"], difficulty=case.difficulty, provenance=case.provenance,
        latency_s=round(latency, 3))

# ---- 12. Case loading & experiment driver -----------------------------
def load_cases(task: str) -> list[Case]:
    fp = CASES_DIR / f"{task}.json"
    rows = json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else []
    cases = [Case(**r) for r in rows]
    if MAX_CASES > 0:
        cases = cases[:MAX_CASES]
    return cases

def run_task(task: str, tiers: Optional[list[str]] = None) -> list[RunRecord]:
    tiers = tiers or RUN_TIERS
    cases = load_cases(task)
    rag = RagIndex(task).build()
    records: list[RunRecord] = []
    for tier in tiers:
        for case in cases:
            for cond in CONDITIONS:
                for r in range(N_REPEATS):
                    records.append(run_once(case, cond, tier, r, rag=rag))
    return records

# ---- 13. Writers ------------------------------------------------------
def save_records(task: str, records: list[RunRecord]) -> tuple[Path, Path]:
    rows = [asdict(r) for r in records]
    jp = TABLES / f"{task}_runs.json"
    jp.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    cp = TABLES / f"{task}_runs.csv"
    if rows:
        keys = list(rows[0].keys())
        with open(cp, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
            for row in rows:
                row = {**row, "cited": "|".join(row["cited"]),
                       "gold_provisions": "|".join(row["gold_provisions"])}
                w.writerow(row)
    return jp, cp

def banner() -> str:
    # Anonymity: never print absolute filesystem paths (they can leak a username).
    return (f"FinGap-Governance | MODE={MODE}\n"
            f"models={MODELS} | tiers={RUN_TIERS} | repeats={N_REPEATS} | "
            f"temp={TEMPERATURE} | top_k={TOP_K} | llm_judge={USE_LLM_JUDGE}"
            + ("\n[!] MOCK MODE — outputs are surrogate, NOT experimental data." if MODE == "mock" else ""))

if __name__ == "__main__":
    print(banner())