"""Experiment Omega -- core library: panel partitioning, research variant generation,
SIMULATED reviewer judgments, a hierarchical pairwise (Bradley-Terry) measurement model
with reviewer random effects, and the causal date-reveal estimator.

HONESTY BOUNDARY (read this): there are NO human reviewers in this environment. Every
"judgment" here is produced by a parameterised reviewer SIMULATION whose ground truth is
quality = blind-tier and integrity-violation = anachronism severity. Consequently the
fitted quality/integrity posteriors and the causal date-effect are conditional on the
simulation's assumptions, not real human data. The value of this module is structural: it
builds the exact measurement+decision apparatus the spec requires and lets us sweep the
*plausible space* of human-utility worlds. Any ship-gate that requires a REAL human
lockbox is therefore unmet by construction (the decision function enforces this).
"""
from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field

sys.path.insert(0, "src")
sys.path.insert(0, "experiments")
import numpy as np  # noqa: E402

from anachronism import is_anachronistic, worst_severity  # noqa: E402
from integrity2 import classify  # noqa: E402

RNG = np.random.default_rng(0)


# ---------------------------------------------------------------- partitioning
def partition_panel(cids: list[str]) -> dict[str, list[str]]:
    """Freeze the 178-panel into discovery / calibration / untouched-lockbox by a stable
    hash of the candidate id (deterministic; no leakage between partitions)."""
    out = {"discovery": [], "calibration": [], "lockbox": []}
    for c in cids:
        h = int(hashlib.md5((c + "|omega").encode()).hexdigest(), 16) % 100
        part = "discovery" if h < 50 else ("calibration" if h < 67 else "lockbox")
        out[part].append(c)
    return out


# ------------------------------------------------------------------- variants
VARIANTS = ["original", "date_hidden", "date_normalized", "skills_only", "career_only", "integrity_evidence"]


def make_variants(cand: dict) -> dict[str, dict]:
    """Research-only profile variants that each isolate a different evidence facet.
    Deterministic transforms of the record; used only to drive the reviewer simulation."""
    import copy
    out = {}
    out["original"] = cand
    dh = copy.deepcopy(cand)
    for j in dh.get("career_history") or []:
        j.pop("start_date", None); j.pop("end_date", None)
    for s in dh.get("skills") or []:
        s["duration_months"] = None
    out["date_hidden"] = dh
    dn = copy.deepcopy(cand)               # clamp impossible durations to plausible
    for s in dn.get("skills") or []:
        if isinstance(s.get("duration_months"), (int, float)) and s["duration_months"] > 42:
            s["duration_months"] = 42
    out["date_normalized"] = dn
    so = copy.deepcopy(cand); so["career_history"] = []          # skills only
    out["skills_only"] = so
    co = copy.deepcopy(cand); co["skills"] = []                  # career only
    out["career_only"] = co
    out["integrity_evidence"] = cand                            # full, integrity in focus
    return out


# ----------------------------------------------------------- latent ground truth
def latent_truth(cand: dict, tier: float) -> tuple[float, float]:
    """(quality, integrity_violation) used as the SIMULATION ground truth.
    quality in [0,1] from blind tier; integrity_violation in [0,~2] from anachronism severity."""
    q = float(tier) / 5.0
    g = worst_severity(cand) if is_anachronistic(cand) else 0.0
    return q, float(g)


# ----------------------------------------------------------- reviewer simulation
@dataclass
class Reviewer:
    rid: int
    quality_sens: float          # how much they reward quality
    integrity_sens: float        # how much they penalise integrity violations (the (A)/(B) axis)
    strictness: float            # baseline severity on integrity ratings
    consistency: float           # 1/noise
    order_bias: float            # preference for first-shown


def make_reviewers(n: int, world_integrity: float) -> list[Reviewer]:
    """A panel whose mean integrity-sensitivity is `world_integrity` (the utility world).
    Heterogeneous around it -> reviewer random effects the model must disentangle."""
    revs = []
    for i in range(n):
        revs.append(Reviewer(
            rid=i,
            quality_sens=float(np.clip(RNG.normal(2.0, 0.4), 0.5, None)),
            integrity_sens=float(np.clip(RNG.normal(world_integrity, 0.6), 0.0, None)),
            strictness=float(RNG.normal(0.0, 0.5)),
            consistency=float(np.clip(RNG.normal(1.0, 0.2), 0.3, None)),
            order_bias=float(RNG.normal(0.0, 0.15)),
        ))
    return revs


@dataclass
class Judgments:
    pairs: list = field(default_factory=list)      # (rid, cid_a, cid_b, winner_a:0/1)
    integ: list = field(default_factory=list)      # (rid, cid, severity_rating, confidence)


def simulate(cands: dict[str, tuple[float, float]], revs: list[Reviewer],
             pairs_per_reviewer: int = 40, variant_of=None) -> Judgments:
    """cands: cid -> (quality, integrity). Each reviewer judges random pairs; integrity
    rating is reviewer-strictness-shifted truth + noise. Enforce: a reviewer never sees two
    variants of the same base candidate (variant_of maps cid->base id)."""
    J = Judgments()
    ids = list(cands)
    for r in revs:
        seen_bases = set()
        tries = 0
        made = 0
        while made < pairs_per_reviewer and tries < pairs_per_reviewer * 6:
            tries += 1
            a, b = RNG.choice(len(ids), size=2, replace=False)
            ca, cb = ids[a], ids[b]
            ba = variant_of.get(ca, ca) if variant_of else ca
            bb = variant_of.get(cb, cb) if variant_of else cb
            if ba in seen_bases or bb in seen_bases or ba == bb:
                continue
            seen_bases.add(ba); seen_bases.add(bb)
            qa, ga = cands[ca]; qb, gb = cands[cb]
            util = (r.quality_sens * (qa - qb) - r.integrity_sens * (ga - gb)
                    + r.order_bias)
            p = 1.0 / (1.0 + np.exp(-r.consistency * util))
            win_a = int(RNG.random() < p)
            J.pairs.append((r.rid, ca, cb, win_a))
            made += 1
        for c in RNG.choice(ids, size=min(20, len(ids)), replace=False):
            q, g = cands[c]
            rating = float(np.clip(g + r.strictness * 0.3 + RNG.normal(0, 0.3 / r.consistency), 0, 3))
            conf = float(np.clip(1.0 - abs(g - 0.5) * 0.3 + RNG.normal(0, 0.1), 0.1, 1.0))
            J.integ.append((r.rid, c, rating, conf))
    return J


# --------------------------------------------- hierarchical Bradley-Terry fit
def fit_bt(cids: list[str], J: Judgments, n_boot: int = 30, l2: float = 1.0):
    """Estimate latent quality theta_c (+ bootstrap interval over reviewers) and integrity
    posterior pi_c from the simulated judgments -- NOT majority vote. BT log-likelihood with
    an L2 prior; reviewer bootstrap gives uncertainty intervals (a hierarchical posterior
    approximation)."""
    from scipy.optimize import minimize
    idx = {c: i for i, c in enumerate(cids)}
    n = len(cids)

    def fit_once(pairs):
        A = np.array([idx[p[1]] for p in pairs]); Bv = np.array([idx[p[2]] for p in pairs])
        y = np.array([p[3] for p in pairs], dtype=float)

        def nll(theta):
            d = theta[A] - theta[Bv]
            p = 1.0 / (1.0 + np.exp(-d))
            p = np.clip(p, 1e-9, 1 - 1e-9)
            ll = y * np.log(p) + (1 - y) * np.log(1 - p)
            g = np.zeros(n)
            np.add.at(g, A, -(y - p)); np.add.at(g, Bv, (y - p))
            return -ll.sum() + l2 * theta @ theta, g + 2 * l2 * theta
        res = minimize(nll, np.zeros(n), jac=True, method="L-BFGS-B")
        return res.x

    theta = fit_once(J.pairs)
    # reviewer bootstrap for intervals
    rids = sorted({p[0] for p in J.pairs})
    boots = []
    for _ in range(n_boot):
        samp = set(RNG.choice(rids, size=len(rids), replace=True).tolist())
        pj = [p for p in J.pairs if p[0] in samp]
        if len(pj) > n:
            boots.append(fit_once(pj))
    boots = np.array(boots) if boots else theta[None, :]
    q_mean = (theta - theta.mean()) / (theta.std() + 1e-9)
    q_lo = np.percentile(boots, 10, axis=0); q_hi = np.percentile(boots, 90, axis=0)
    q_lo = (q_lo - theta.mean()) / (theta.std() + 1e-9)
    q_hi = (q_hi - theta.mean()) / (theta.std() + 1e-9)

    # integrity posterior: reviewer-strictness-adjusted mean rating -> prob(hard)
    from collections import defaultdict
    rat = defaultdict(list)
    for rid, c, s, conf in J.integ:
        rat[c].append(s * conf)
    pi = np.array([np.mean(rat[c]) if rat[c] else 0.0 for c in cids])
    pi_std = np.array([np.std(rat[c]) if len(rat[c]) > 1 else 0.5 for c in cids])
    pi_prob = 1.0 / (1.0 + np.exp(-(pi - 1.0) * 2.0))           # sev>1 -> likely hard
    return {"cids": cids, "q_mean": q_mean, "q_lo": np.minimum(q_lo, q_hi),
            "q_hi": np.maximum(q_lo, q_hi), "pi_prob": pi_prob, "pi_std": pi_std}


def soft_pairwise_accuracy(cids, q, J: Judgments) -> float:
    """SPA: fraction of held-out pairs whose simulated winner matches the model's quality
    order, weighted by |quality gap| (confident pairs count more)."""
    idx = {c: i for i, c in enumerate(cids)}
    num = den = 0.0
    for rid, a, b, win_a in J.pairs:
        if a not in idx or b not in idx:
            continue
        gap = abs(q[idx[a]] - q[idx[b]])
        pred_a = q[idx[a]] > q[idx[b]]
        num += gap * (1.0 if pred_a == bool(win_a) else 0.0)
        den += gap
    return num / den if den else 0.0
