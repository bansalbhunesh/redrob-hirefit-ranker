"""Shared harness for competitor-idea experiments. Every signal is holdout-gated:
blend/apply it, choose the strength on a TRAIN label half, report the gain on an
untouched TEST half. In-sample gains that fail the holdout are rejected.
"""
import hashlib
import pickle
import statistics
import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
from redrob_ranker.eval_harness import load_labels, evaluate, LabelSet

_CACHE = {}


def load_pool():
    d = pickle.load(open("experiments/_pool.pkl", "rb"))
    return d["recs"], d["base_ids"]


def minmax(x):
    x = np.asarray(x, dtype=float)
    lo, hi = float(x.min()), float(x.max())
    return (x - lo) / (hi - lo) if hi > lo else np.full_like(x, 0.5)


def labels():
    if "full" not in _CACHE:
        full = load_labels(Path("artifacts/h2_availblind_labels.jsonl"))

        def b(c):
            return int(hashlib.md5(c.encode()).hexdigest(), 16) % 2
        tr = {c: v for c, v in full.tiers.items() if b(c) == 0}
        te = {c: v for c, v in full.tiers.items() if b(c) == 1}
        _CACHE["full"] = full
        _CACHE["train"] = LabelSet("train", tr, {c: full.gains[c] for c in tr})
        _CACHE["test"] = LabelSet("test", te, {c: full.gains[c] for c in te})
    return _CACHE["full"], _CACHE["train"], _CACHE["test"]


def _ranktop(cids, final):
    order = sorted(range(len(cids)), key=lambda i: (-final[i], cids[i]))
    return [cids[i] for i in order[:100]]


def gate(recs, base_ids, scores, name, mode="blend", weights=None):
    """mode='blend': final=(1-w)*hand_n + w*minmax(scores); scores = positive signal.
       mode='mult':  final=hand * (scores**w); scores = per-candidate factor (1=neutral)."""
    full, train, test = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    hand_n = minmax(hand)
    base_f = evaluate(base_ids, full).composite
    base_tr = evaluate(base_ids, train).composite
    base_te = evaluate(base_ids, test).composite
    if weights is None:
        weights = [0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40] if mode == "blend" else [0.0, 0.5, 1.0, 1.5, 2.0]
    sig_n = minmax(scores) if mode == "blend" else np.asarray(scores, dtype=float)
    rows = []
    for w in weights:
        if mode == "blend":
            final = (1 - w) * hand_n + w * sig_n
        else:
            final = hand * np.power(np.clip(sig_n, 1e-6, None), w)
        top = _ranktop(cids, final)
        rows.append((w, evaluate(top, full).composite, evaluate(top, train).composite, evaluate(top, test).composite))
    wstar = max(rows, key=lambda r: r[2])  # choose strength on TRAIN only
    print(f"\n=== {name} ({mode}) ===")
    print(f"baseline: full={base_f:.4f} train={base_tr:.4f} test={base_te:.4f}")
    print(f'{"w":>6}{"full":>9}{"train":>9}{"test":>9}{"test-base":>11}')
    for w, f, tr, te in rows:
        print(f"{w:>6.2f}{f:>9.4f}{tr:>9.4f}{te:>9.4f}{te-base_te:>+11.4f}")
    holdout_delta = wstar[3] - base_te
    verdict = "GENERALIZES" if holdout_delta > 1e-4 else "rejected (in-sample only)"
    print(f"w* (on train)={wstar[0]}  ->  HOLDOUT delta {holdout_delta:+.4f}  [{verdict}]")
    return {"name": name, "wstar": wstar[0], "holdout_delta": holdout_delta,
            "best_full": max(r[1] for r in rows), "base_full": base_f, "verdict": verdict}


def gate_cv(recs, base_ids, scores, name, mode="blend", k=5, weights=None):
    """5-fold CV: per fold, pick strength on the other k-1 folds, score the held-out fold.
    Robust verdict = mean & worst-case (min) test delta across folds."""
    full, _, _ = labels()
    foldof = {c: int(hashlib.md5(c.encode()).hexdigest(), 16) % k for c in full.tiers}
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    hand_n = minmax(hand)
    sig_n = minmax(scores) if mode == "blend" else np.asarray(scores, dtype=float)
    if weights is None:
        weights = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40] if mode == "blend" else [0.5, 1.0, 2.0, 3.0]

    def final_for(w):
        if mode == "blend":
            return (1 - w) * hand_n + w * sig_n
        return hand * np.power(np.clip(sig_n, 1e-6, None), w)

    deltas, chosen = [], []
    for f in range(k):
        tr_t = {c: v for c, v in full.tiers.items() if foldof[c] != f}
        te_t = {c: v for c, v in full.tiers.items() if foldof[c] == f}
        TR = LabelSet("tr", tr_t, {c: full.gains[c] for c in tr_t})
        TE = LabelSet("te", te_t, {c: full.gains[c] for c in te_t})
        base_te = evaluate(base_ids, TE).composite
        best = None
        for w in weights:
            top = _ranktop(cids, final_for(w))
            trc = evaluate(top, TR).composite
            if best is None or trc > best[0]:
                best = (trc, w, top)
        deltas.append(evaluate(best[2], TE).composite - base_te)
        chosen.append(best[1])
    res = {"name": name, "mean": statistics.mean(deltas), "min": min(deltas),
           "deltas": [round(d, 4) for d in deltas], "w_modes": chosen}
    robust = "ROBUST+" if res["mean"] > 1e-4 and res["min"] >= -5e-4 else (
        "mean+ but unstable" if res["mean"] > 1e-4 else "rejected")
    print(f"{name:<40} CV mean {res['mean']:+.4f}  min {res['min']:+.4f}  folds {res['deltas']}  [{robust}]")
    res["robust"] = robust
    return res


def gate_repeat(recs, base_ids, scores, name, mode="blend", R=12, weights=None):
    """R repeated 50/50 splits (less noisy than 1/5 folds). Pick strength on each train
    half, score the test half. Report mean, std, and fraction-positive across repeats."""
    full, _, _ = labels()
    cids = [r["cid"] for r in recs]
    hand = np.array([r["hand"] for r in recs], dtype=float)
    hand_n = minmax(hand)
    sig_n = minmax(scores) if mode == "blend" else np.asarray(scores, dtype=float)
    if weights is None:
        weights = [0.05, 0.10, 0.15, 0.20, 0.30, 0.40] if mode == "blend" else [0.5, 1.0, 2.0]

    def final_for(w):
        if mode == "blend":
            return (1 - w) * hand_n + w * sig_n
        return hand * np.power(np.clip(sig_n, 1e-6, None), w)

    deltas = []
    for s in range(R):
        tr, te = {}, {}
        for c, val in full.tiers.items():
            if int(hashlib.md5((c + "|" + str(s)).encode()).hexdigest(), 16) % 2 == 0:
                tr[c] = val
            else:
                te[c] = val
        TR = LabelSet("tr", tr, {c: full.gains[c] for c in tr})
        TE = LabelSet("te", te, {c: full.gains[c] for c in te})
        base_te = evaluate(base_ids, TE).composite
        best = None
        for w in weights:
            top = _ranktop(cids, final_for(w))
            trc = evaluate(top, TR).composite
            if best is None or trc > best[0]:
                best = (trc, top)
        deltas.append(evaluate(best[1], TE).composite - base_te)
    arr = np.array(deltas)
    pos = int((arr > 0).sum())
    print(f"{name:<34} mean {arr.mean():+.4f}  std {arr.std():.4f}  pos {pos}/{R}  min {arr.min():+.4f}  max {arr.max():+.4f}")
    return {"name": name, "mean": float(arr.mean()), "std": float(arr.std()), "pos": pos, "R": R}
