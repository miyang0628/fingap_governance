# ======================================================================
# _build_artifacts.py
# FinGap-Governance | Generator for corpus / provision-judgment graph /
# case bank. Imported and executed by notebook 01. Kept as a module so the
# authored content is version-controlled and diffable on GitHub.
# All content is research-authored and PII-free. Provision "text" entries
# are plain-language summaries authored by the research team; replace them
# with full licensed statutory text locally if required (not redistributed).
# ======================================================================
from __future__ import annotations
import json
from pathlib import Path
from fingap_core import CORPUS_DIR, GRAPH_DIR, CASES_DIR

# ---------------------------------------------------------------- CORPUS
# Each task corpus includes the GOVERNING provisions AND distractors, so
# vanilla retrieval is non-trivial (a relevant-looking chunk is not
# necessarily the grounding provision).
CORPUS = {
    "advisory": [
        {"provision_id": "FCPA-Art17", "label": "FCPA Art. 17 (suitability)",
         "text": "Where a financial product is recommended or solicited to a retail client, "
                 "the firm must first ascertain the client's status, financial situation, and "
                 "investment experience, and must not recommend a product found unsuitable in "
                 "light of that assessment. The suitability duty is triggered by an act of "
                 "solicitation or recommendation toward a specific product."},
        {"provision_id": "FCPA-Art18", "label": "FCPA Art. 18 (appropriateness)",
         "text": "Where a retail client, on the client's own initiative and without "
                 "solicitation, seeks to enter into a non-recommended product, the firm must "
                 "verify the client's information and warn the client if the product is "
                 "inappropriate. The appropriateness duty applies to information-only, "
                 "client-initiated transactions where no specific product was recommended."},
        {"provision_id": "FCPA-Art19", "label": "FCPA Art. 19 (duty to explain)",
         "text": "When concluding a contract, the firm must explain the key terms, risks, and "
                 "costs of the product so that the client understands them, and obtain "
                 "confirmation. The explanation duty attaches to contract conclusion regardless "
                 "of who initiated the transaction."},
        {"provision_id": "FCPA-Art20", "label": "FCPA Art. 20 (unfair business conduct)",
         "text": "A firm must not exploit its superior position to compel a client to enter "
                 "transactions unrelated to the client's needs, tie unnecessary products, or "
                 "otherwise engage in unfair business conduct."},
        {"provision_id": "FCPA-Art21", "label": "FCPA Art. 21 (improper solicitation)",
         "text": "A firm must not provide false information, assert uncertain matters as "
                 "certain, or solicit without the client's request for certain high-risk "
                 "products (unsolicited-call prohibition)."},
        {"provision_id": "FCPA-Art22", "label": "FCPA Art. 22 (advertising regulation)",
         "text": "Advertising of financial products must be fair and not misleading, must "
                 "include statutory risk disclosures, and must pass internal review before "
                 "publication."},
    ],
    "anomaly": [
        {"provision_id": "TFTIA-Art4", "label": "TFTIA Art. 4 (Suspicious Transaction Report)",
         "text": "Where there are reasonable grounds to suspect that assets received are "
                 "illegal property or that a counterpart is engaged in money laundering, the "
                 "institution must report the suspicious transaction regardless of amount. "
                 "Structuring deposits to evade reporting thresholds is itself a ground for "
                 "suspicion."},
        {"provision_id": "TFTIA-Art4-2", "label": "TFTIA Art. 4-2 (Currency Transaction Report)",
         "text": "An institution must report cash transactions to the Financial Intelligence "
                 "Unit when the cash paid or received meets or exceeds the prescribed threshold "
                 "within the prescribed period. The currency transaction report is threshold-"
                 "based and does not require any suspicion."},
        {"provision_id": "TFTIA-Enf-Art8-2", "label": "TFTIA Enf. Decree Art. 8-2 (threshold)",
         "text": "The currency transaction reporting threshold is cash of KRW 10 million or "
                 "more, aggregated per person within one business day. Transactions split "
                 "across more than one business day are not aggregated under this threshold."},
        {"provision_id": "TFTIA-Art2-4", "label": "TFTIA Art. 2(4) (definition of money laundering)",
         "text": "Money laundering means the act of disguising or concealing the acquisition or "
                 "disposition of criminal proceeds or their origin."},
    ],
    "accounting": [
        {"provision_id": "KIFRS1115-P35", "label": "K-IFRS 1115 para. 35 (over time)",
         "text": "An entity recognises revenue over time if one of three criteria is met: (1) "
                 "the customer simultaneously receives and consumes the benefits as the entity "
                 "performs; (2) the entity's performance creates or enhances an asset the "
                 "customer controls; or (3) the entity's performance does not create an asset "
                 "with an alternative use and the entity has an enforceable right to payment for "
                 "performance completed to date."},
        {"provision_id": "KIFRS1115-P35-3", "label": "K-IFRS 1115 para. 35(3) (no alt use + right to payment)",
         "text": "Under the third over-time criterion, the asset has no alternative use to the "
                 "entity if the entity is restricted from redirecting it, AND the entity holds "
                 "an enforceable right to payment for performance completed to date including a "
                 "reasonable margin. BOTH conditions must hold; the absence of an enforceable "
                 "right to payment defeats over-time recognition under this criterion."},
        {"provision_id": "KIFRS1115-P38", "label": "K-IFRS 1115 para. 38 (point in time)",
         "text": "If a performance obligation is not satisfied over time, it is satisfied at a "
                 "point in time; the entity recognises revenue when the customer obtains "
                 "control of the asset, considering indicators such as present right to payment, "
                 "legal title, physical possession, risks and rewards, and acceptance."},
        {"provision_id": "KIFRS1018", "label": "K-IFRS 1018 (superseded)",
         "text": "Former revenue standard superseded by K-IFRS 1115. Retained here only to test "
                 "citation of outdated standards; must not be cited as the current basis."},
        {"provision_id": "KIFRS1011", "label": "K-IFRS 1011 (construction contracts, superseded)",
         "text": "Former construction-contract standard superseded by K-IFRS 1115. Must not be "
                 "cited as the current basis for construction revenue."},
    ],
}

# ----------------------------------------------------------------- GRAPH
# The provision-judgment graph encodes GENERAL trigger conditions, not the
# answer to any specific case. The model must still perform the subsumption.
GRAPH = {
    "advisory": {
        "provision_nodes": [
            {"id": "FCPA-Art17", "label": "FCPA Art. 17 (suitability)", "status": "current"},
            {"id": "FCPA-Art18", "label": "FCPA Art. 18 (appropriateness)", "status": "current"},
            {"id": "FCPA-Art19", "label": "FCPA Art. 19 (duty to explain)", "status": "current"},
            {"id": "FCPA-Art22", "label": "FCPA Art. 22 (advertising)", "status": "current"},
        ],
        "judgment_edges": [
            {"condition": "the firm recommended or solicited a specific product to the client",
             "determination": "suitability", "provision_id": "FCPA-Art17", "priority": 2},
            {"condition": "the client initiated the transaction and no specific product was recommended (information only)",
             "determination": "appropriateness", "provision_id": "FCPA-Art18", "priority": 1},
            {"condition": "the matter concerns misleading advertising rather than an individual transaction",
             "determination": "none", "provision_id": "FCPA-Art22", "priority": 0},
        ],
        "supersession_edges": [],
    },
    "anomaly": {
        "provision_nodes": [
            {"id": "TFTIA-Art4", "label": "TFTIA Art. 4 (STR)", "status": "current"},
            {"id": "TFTIA-Art4-2", "label": "TFTIA Art. 4-2 (CTR)", "status": "current"},
            {"id": "TFTIA-Enf-Art8-2", "label": "TFTIA Enf. Decree Art. 8-2 (KRW 10M / 1 business day)", "status": "current"},
        ],
        "judgment_edges": [
            {"condition": "there are reasonable grounds to suspect money laundering, including deposits structured to stay below the threshold",
             "determination": "STR", "provision_id": "TFTIA-Art4", "priority": 2},
            {"condition": "cash of KRW 10 million or more is paid or received, aggregated per person within one business day, with no suspicion",
             "determination": "CTR", "provision_id": "TFTIA-Art4-2", "priority": 1},
            {"condition": "cash is below the threshold or split across more than one business day and there is no suspicion",
             "determination": "none", "provision_id": "TFTIA-Art4-2", "priority": 0},
        ],
        "supersession_edges": [],
    },
    "accounting": {
        "provision_nodes": [
            {"id": "KIFRS1115-P35", "label": "K-IFRS 1115 para. 35 (over time)", "status": "current"},
            {"id": "KIFRS1115-P35-3", "label": "K-IFRS 1115 para. 35(3) (no alt use + right to payment)", "status": "current"},
            {"id": "KIFRS1115-P38", "label": "K-IFRS 1115 para. 38 (point in time)", "status": "current"},
            {"id": "KIFRS1018", "label": "K-IFRS 1018 (superseded)", "status": "superseded"},
            {"id": "KIFRS1011", "label": "K-IFRS 1011 (superseded)", "status": "superseded"},
        ],
        "judgment_edges": [
            {"condition": "the asset has no alternative use to the entity AND the entity has an enforceable right to payment for performance to date",
             "determination": "over_time", "provision_id": "KIFRS1115-P35-3", "priority": 3},
            {"condition": "the customer controls the asset as it is created or consumes benefits as the entity performs",
             "determination": "over_time", "provision_id": "KIFRS1115-P35", "priority": 2},
            {"condition": "no over-time criterion is met (e.g. no alternative use but NO enforceable right to payment, or a standard good is delivered)",
             "determination": "point_in_time", "provision_id": "KIFRS1115-P38", "priority": 1},
        ],
        "supersession_edges": [
            {"old": "KIFRS1018", "new": "KIFRS1115-P35"},
            {"old": "KIFRS1011", "new": "KIFRS1115-P35"},
        ],
    },
}

# ------------------------------------------------------------ CASE BANK
# difficulty: clear | boundary | distractor.  provenance: research_authored.
# expert_adjudicated/adjudicator are filled by a domain expert before the
# runs count as validated evidence (left False here by design).
def _c(cid, task, axis, facts, det, prov, cond, diff, prov_src="research_authored", notes=""):
    return {"case_id": cid, "task": task, "boundary_axis": axis, "facts": facts,
            "gold_determination": det, "gold_provisions": prov,
            "discriminating_condition": cond, "difficulty": diff,
            "provenance": prov_src, "expert_adjudicated": False, "adjudicator": "", "notes": notes}

CASES = {"advisory": [], "anomaly": [], "accounting": []}

# --- advisory ---------------------------------------------------------
_adv = CASES["advisory"]
_adv += [
 _c("ADV-01","advisory","solicitation vs information-only",
    "A branch employee proactively recommended a specific equity-linked fund to a walk-in retail "
    "client and urged the client to subscribe that day. No prior risk profiling was done.",
    "suitability",["FCPA-Art17"],"the firm recommended a specific product (solicitation)","clear"),
 _c("ADV-02","advisory","solicitation vs information-only",
    "A client called asking general questions about how index funds work. The employee explained "
    "the concept, recommended nothing, and the client opened an account later on their own.",
    "appropriateness",["FCPA-Art18"],"client initiated, information only, no specific product recommended","clear"),
 _c("ADV-03","advisory","solicitation vs information-only",
    "A client asked broadly about 'something with higher returns.' The employee replied only with "
    "general categories, naming no product, and did not suggest subscribing.",
    "appropriateness",["FCPA-Art18"],"no specific product recommended, information only","boundary"),
 _c("ADV-04","advisory","solicitation vs information-only",
    "After the client asked a general question, the employee steered the conversation to one named "
    "structured note and encouraged the client to buy it.",
    "suitability",["FCPA-Art17"],"employee pointed to a specific product and encouraged purchase","boundary"),
 _c("ADV-05","advisory","advertising vs individual transaction",
    "A consumer complained that a bank's online banner for a savings product omitted the risk "
    "disclosure. No individual recommendation or transaction was involved.",
    "none",["FCPA-Art22"],"misleading advertising, not an individual transaction","distractor"),
 _c("ADV-06","advisory","solicitation vs information-only",
    "A private-banking manager recommended a complex derivative-linked product to an elderly client "
    "and pressed for immediate subscription without assessing suitability.",
    "suitability",["FCPA-Art17"],"specific product recommended/solicited to the client","clear"),
]
# parameterized variants to broaden n (vary actor/product while keeping the axis)
for i,(actor,prod,solicit) in enumerate([
    ("a teller","a specific overseas-bond fund",True),
    ("a call-center agent","a named variable annuity",True),
    ("a mobile-app chatbot","a general product category",False),
    ("a relationship manager","no specific product (only categories)",False),
    ("a branch manager","a specific high-yield note",True),
    ("an online advisor","a general explanation of ETFs",False),
], start=7):
    det,prov,cond,diff = (("suitability",["FCPA-Art17"],"a specific product was recommended (solicitation)","clear")
        if solicit else ("appropriateness",["FCPA-Art18"],"client initiated, no specific product recommended","clear"))
    _adv.append(_c(f"ADV-{i:02d}","advisory","solicitation vs information-only",
        f"{actor.capitalize()} interacted with a retail client regarding {prod}. "
        + ("The client had asked only a general question and received information with no specific recommendation."
           if not solicit else "The interaction centred on recommending that specific product to the client."),
        det,prov,cond,diff))
_adv += [
 _c("ADV-13","advisory","explain-duty overlay",
    "A firm recommended a specific complex product (clear solicitation) but the dispute is solely about "
    "whether the key risks were explained at contract signing.",
    "suitability",["FCPA-Art17"],"a specific product was recommended (solicitation governs the primary duty)","boundary",
    notes="Art.19 explain-duty co-applies; gold primary duty is suitability under Art.17."),
 _c("ADV-14","advisory","solicitation vs information-only",
    "A client initiated a purchase of a plain term deposit with no advice sought or given.",
    "appropriateness",["FCPA-Art18"],"client-initiated, information-only transaction","clear"),
 _c("ADV-15","advisory","solicitation vs information-only",
    "An employee recommended a specific leveraged ETF to a novice client who had asked for 'safe options.'",
    "suitability",["FCPA-Art17"],"a specific product was recommended to the client","clear"),
 _c("ADV-16","advisory","advertising vs individual transaction",
    "A marketing email blast promoted a fund with an exaggerated return claim to a mailing list.",
    "none",["FCPA-Art22"],"advertising content issue, not an individual recommendation","distractor"),
 _c("ADV-17","advisory","solicitation vs information-only",
    "A client asked to compare two products they had already chosen; the employee gave neutral factual "
    "comparisons and recommended neither.",
    "appropriateness",["FCPA-Art18"],"no recommendation of a specific product; information only","boundary"),
 _c("ADV-18","advisory","solicitation vs information-only",
    "A wealth advisor built a portfolio and explicitly recommended three specific funds for the client to buy.",
    "suitability",["FCPA-Art17"],"specific products were recommended (solicitation)","clear"),
]

# --- anomaly ----------------------------------------------------------
_ano = CASES["anomaly"]
_ano += [
 _c("ANO-01","anomaly","STR vs CTR",
    "A customer deposited KRW 15,000,000 in cash in a single transaction in one business day. "
    "There was nothing otherwise suspicious about the customer or the funds.",
    "CTR",["TFTIA-Art4-2","TFTIA-Enf-Art8-2"],"cash of KRW 10M or more aggregated within one business day, no suspicion","clear"),
 _c("ANO-02","anomaly","STR vs CTR (structuring)",
    "Within the same business day a customer made four cash deposits of KRW 4,000,000 each at "
    "different branches, and the stated purpose did not match the account's usual activity.",
    "STR",["TFTIA-Art4"],"deposits structured below the threshold with a purpose mismatch (suspicion of money laundering)","boundary"),
 _c("ANO-03","anomaly","STR vs none",
    "A small wire of KRW 900,000 was sent, but the sender's documents were forged and the funds "
    "appeared linked to an illegal scheme.",
    "STR",["TFTIA-Art4"],"reasonable grounds to suspect money laundering regardless of amount","clear"),
 _c("ANO-04","anomaly","CTR vs none",
    "A company's verified payroll cash withdrawal of KRW 20,000,000 occurred in one business day. "
    "Documentation was complete and nothing was suspicious.",
    "CTR",["TFTIA-Art4-2","TFTIA-Enf-Art8-2"],"cash of KRW 10M or more within one business day, no suspicion","clear"),
 _c("ANO-05","anomaly","threshold timing",
    "A customer deposited KRW 7,000,000 in cash on Monday and KRW 7,000,000 on Tuesday. There was "
    "no indication of suspicion and no apparent attempt to evade reporting.",
    "none",["TFTIA-Art4-2"],"cash split across more than one business day, threshold not aggregated, no suspicion","boundary"),
 _c("ANO-06","anomaly","STR vs CTR (structuring)",
    "A customer made three cash deposits of KRW 3,500,000 within an hour across two branches and "
    "asked staff whether deposits 'under the limit' are reported.",
    "STR",["TFTIA-Art4"],"structuring to evade the threshold is itself a ground for suspicion","boundary"),
]
for i,(amt,same_day,susp) in enumerate([
    (12_000_000,True,False),(9_500_000,True,False),(50_000_000,True,False),
    (6_000_000,False,False),(2_000_000,True,True),(30_000_000,True,False),
], start=7):
    if susp:
        det,prov,cond,diff = "STR",["TFTIA-Art4"],"reasonable grounds to suspect money laundering regardless of amount","clear"
        facts=f"A cash transaction of KRW {amt:,} occurred with clear indicators of money laundering."
    elif amt>=10_000_000 and same_day:
        det,prov,cond,diff = "CTR",["TFTIA-Art4-2","TFTIA-Enf-Art8-2"],"cash of KRW 10M or more within one business day, no suspicion","clear"
        facts=f"A customer transacted KRW {amt:,} in cash within one business day with no suspicious indicators."
    else:
        det,prov,cond,diff = "none",["TFTIA-Art4-2"],"cash below threshold or not aggregated within one business day, no suspicion","clear"
        facts=f"A customer transacted KRW {amt:,} in cash" + (" within one business day" if same_day else " split across two business days") + " with no suspicious indicators."
    _ano.append(_c(f"ANO-{i:02d}","anomaly","STR vs CTR vs none",facts,det,prov,cond,diff))
_ano += [
 _c("ANO-13","anomaly","STR vs CTR",
    "A customer deposited KRW 11,000,000 in cash in one business day; separately, the branch noted the "
    "customer's explanations were inconsistent and possibly concealing the source.",
    "STR",["TFTIA-Art4"],"suspicion of money laundering takes priority over the threshold report","boundary",
    notes="Both CTR threshold and STR suspicion present; STR governs as the higher-priority duty."),
 _c("ANO-14","anomaly","CTR vs none",
    "A single cash deposit of exactly KRW 10,000,000 was made in one business day with no suspicion.",
    "CTR",["TFTIA-Art4-2","TFTIA-Enf-Art8-2"],"cash meets the KRW 10M threshold within one business day","clear"),
 _c("ANO-15","anomaly","none",
    "A customer made an electronic (non-cash) transfer of KRW 40,000,000 between their own verified "
    "accounts with no suspicion.",
    "none",["TFTIA-Art4-2"],"non-cash transfer does not meet the currency transaction report and no suspicion","distractor"),
 _c("ANO-16","anomaly","STR",
    "Multiple third parties deposited small cash amounts into one account that were immediately wired "
    "overseas, a pattern consistent with layering.",
    "STR",["TFTIA-Art4"],"layering pattern gives reasonable grounds to suspect money laundering","clear"),
 _c("ANO-17","anomaly","threshold timing",
    "A customer deposited KRW 8,000,000 cash in the morning and KRW 8,000,000 cash in the afternoon of "
    "the same business day with no suspicion.",
    "CTR",["TFTIA-Art4-2","TFTIA-Enf-Art8-2"],"cash aggregated per person within one business day meets the threshold","boundary"),
 _c("ANO-18","anomaly","none",
    "A customer paid KRW 500,000 in cash for a routine fee with complete documentation and no suspicion.",
    "none",["TFTIA-Art4-2"],"cash far below threshold and no suspicion","distractor"),
]

# --- accounting -------------------------------------------------------
_acc = CASES["accounting"]
_acc += [
 _c("ACC-01","accounting","over-time vs point-in-time",
    "A contractor builds a customized factory on the customer's land; the customer controls the "
    "work-in-progress throughout construction.",
    "over_time",["KIFRS1115-P35"],"the customer controls the asset as it is created","clear"),
 _c("ACC-02","accounting","over-time vs point-in-time",
    "A manufacturer produces a bespoke machine with no alternative use and holds an enforceable right "
    "to payment for work completed to date including margin.",
    "over_time",["KIFRS1115-P35-3"],"no alternative use AND an enforceable right to payment for performance to date","clear"),
 _c("ACC-03","accounting","over-time vs point-in-time",
    "A manufacturer builds a highly customized asset with no alternative use, but the contract gives "
    "NO enforceable right to payment for performance completed to date if the customer cancels.",
    "point_in_time",["KIFRS1115-P38"],"no alternative use but NO enforceable right to payment, so the over-time criterion fails","boundary"),
 _c("ACC-04","accounting","over-time vs point-in-time",
    "A retailer sells standard off-the-shelf appliances shipped to customers.",
    "point_in_time",["KIFRS1115-P38"],"a standard good with alternative use is delivered; control transfers at a point in time","clear"),
 _c("ACC-05","accounting","supersession trap",
    "A construction firm's analyst drafts a memo recognizing revenue on a long-term contract and "
    "wants to cite the old construction-contract standard as the basis.",
    "over_time",["KIFRS1115-P35"],"current standard governs; the superseded construction standard must not be cited","distractor",
    notes="Tests supersession/hallucination: KIFRS1011/1018 must not be cited as current."),
 _c("ACC-06","accounting","over-time vs point-in-time",
    "A cleaning company provides daily office cleaning under an annual contract; the customer consumes "
    "the benefit as the service is performed.",
    "over_time",["KIFRS1115-P35"],"the customer simultaneously receives and consumes the benefits as the entity performs","clear"),
]
for i,(no_alt,right,controls,standard) in enumerate([
    (True,True,False,False),(True,False,False,False),(False,False,False,True),
    (False,False,True,False),(True,True,False,False),(False,False,False,True),
], start=7):
    if controls:
        det,prov,cond,diff="over_time",["KIFRS1115-P35"],"the customer controls the asset as it is created","clear"
        facts="The entity enhances an asset that the customer controls throughout performance."
    elif no_alt and right:
        det,prov,cond,diff="over_time",["KIFRS1115-P35-3"],"no alternative use AND an enforceable right to payment to date","clear"
        facts="The entity builds an asset with no alternative use and holds an enforceable right to payment for work to date."
    elif no_alt and not right:
        det,prov,cond,diff="point_in_time",["KIFRS1115-P38"],"no alternative use but NO enforceable right to payment, over-time criterion fails","boundary"
        facts="The asset has no alternative use, but there is no enforceable right to payment for performance completed to date."
    else:
        det,prov,cond,diff="point_in_time",["KIFRS1115-P38"],"a standard good with alternative use transfers control at a point in time","clear"
        facts="The entity sells a standard product with alternative use, delivered to the customer."
    _acc.append(_c(f"ACC-{i:02d}","accounting","over-time vs point-in-time",facts,det,prov,cond,diff))
_acc += [
 _c("ACC-13","accounting","over-time vs point-in-time",
    "A software firm delivers a perpetual off-the-shelf license with no further obligations.",
    "point_in_time",["KIFRS1115-P38"],"control of a standard license transfers at a point in time","clear"),
 _c("ACC-14","accounting","over-time vs point-in-time",
    "An engineering firm constructs a custom bridge on public land with an enforceable right to payment "
    "for work to date and no alternative use of the partially built structure.",
    "over_time",["KIFRS1115-P35-3"],"no alternative use AND enforceable right to payment to date","clear"),
 _c("ACC-15","accounting","boundary right-to-payment",
    "A shipbuilder constructs a specialized vessel with no alternative use; the contract allows the buyer "
    "to cancel with only a nominal fee that does not cover work to date.",
    "point_in_time",["KIFRS1115-P38"],"no alternative use but the right to payment is not enforceable for work to date","boundary"),
 _c("ACC-16","accounting","supersession trap",
    "An analyst prepares revenue recognition for a service contract and considers citing a superseded "
    "revenue standard alongside the current one.",
    "over_time",["KIFRS1115-P35"],"only the current standard grounds the determination; superseded standards must not be cited","distractor"),
 _c("ACC-17","accounting","over-time vs point-in-time",
    "A consultancy delivers a one-off report; the customer obtains the benefit only upon final delivery "
    "and acceptance.",
    "point_in_time",["KIFRS1115-P38"],"benefit is obtained only at final delivery/acceptance, not continuously","boundary"),
 _c("ACC-18","accounting","over-time vs point-in-time",
    "A telecom provides monthly network service that the customer consumes continuously over the contract.",
    "over_time",["KIFRS1115-P35"],"the customer consumes the benefit continuously as the entity performs","clear"),
]

def write_all() -> dict:
    counts = {}
    for task, docs in CORPUS.items():
        (CORPUS_DIR / f"{task}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    for task, g in GRAPH.items():
        (GRAPH_DIR / f"{task}.json").write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
    for task, cs in CASES.items():
        (CASES_DIR / f"{task}.json").write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
        counts[task] = len(cs)
    return counts

if __name__ == "__main__":
    print("case counts:", write_all())
