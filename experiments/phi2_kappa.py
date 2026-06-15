"""Phi-2 intercoder reliability harness. Computes Cohen's kappa (evidence/action) and
weighted kappa (severity) between coder_1 (corpus_phi2.csv) and a REAL second coder
(second_coder_responses.jsonl: {item_id, evidence_status, hiring_action, severity}).
AWAITING a real independent human coder -- self-coding a 2nd pass would NOT be valid IRR."""
import csv, json, sys
from pathlib import Path
OUT=Path("docs/human_opinion")
def main():
    f=OUT/"second_coder_responses.jsonl"
    if not f.exists() or not f.read_text().strip():
        print("AWAITING_SECOND_CODER: docs/human_opinion/second_coder_responses.jsonl is empty.")
        print("Give a real independent coder the de-identified second_coder_packet.jsonl + codebook_v2.md")
        print("(no coder_1 labels, no expected conclusion). Then this computes:")
        print("  Cohen's kappa: included/excluded, evidence_status, hiring_action")
        print("  weighted kappa: severity 0-4 ;  per-label: red_flag_type")
        print("Interpretation guide (NOT auto-validity): <0.40 weak / 0.40-0.60 moderate / "
              "0.60-0.80 substantial / >0.80 strong. Report axes SEPARATELY (do not collapse).")
        return
    from sklearn.metrics import cohen_kappa_score
    c1={r["item_id"]:r for r in csv.DictReader(open(OUT/"corpus_phi2.csv",encoding="utf-8"))}
    c2={json.loads(l)["item_id"]:json.loads(l) for l in open(f,encoding="utf-8")}
    ids=[i for i in c1 if i in c2]
    for var in ("evidence_status","hiring_action"):
        a=[c1[i][var] for i in ids]; b=[c2[i][var] for i in ids]
        print(f"{var}: Cohen kappa = {cohen_kappa_score(a,b):.3f}  (n={len(ids)})")
    a=[int(c1[i]["severity"]) for i in ids]; b=[int(c2[i]["severity"]) for i in ids]
    print(f"severity: weighted kappa = {cohen_kappa_score(a,b,weights='quadratic'):.3f}")
if __name__=="__main__": main()
