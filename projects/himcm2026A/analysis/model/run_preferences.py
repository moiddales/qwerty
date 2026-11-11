"""Robust analysis under stated preferences (Theta_PLAN) and ELECTRE III with sampled weights.

    cd projects/himcm2026A/analysis/model && python run_preferences.py
"""
import json
import numpy as np
import pandas as pd
from core import (Model, SPEC_M2, STATEMENTS_PLAN, DOMAINS, RES, load, fill_missing, ranks, electre, distill, final_order)

rng = np.random.default_rng(42)
names, X, S = load()
CITY, CID, nC = names.values, names.index, len(names)
OUT = {}


def noisy_U(M, thetas):
    x = X[M.inds].values.astype(float); s = S[M.inds].values.astype(float)
    n = len(thetas); out = []
    for a in range(0, n, 500):
        k = min(500, n - a)
        d = x[None] + rng.standard_normal((k,) + x.shape) * s[None]
        for j in range(M.m):
            miss = np.isnan(x[:, j])
            if miss.any():
                d[:, miss, j] = rng.choice(x[~miss, j], size=(k, miss.sum()))
        out.append(np.einsum("nck,nk->nc", M.phi(d.reshape(-1, M.m)).reshape(k, nC, M.n), thetas[a:a + k]))
    return np.vstack(out)


def robust(M, tag):
    PH = M.phi(fill_missing(X[M.inds]).values)
    dmax = np.zeros((nC, nC))
    for a in range(nC):
        for b in range(nC):
            if a != b:
                dmax[a, b] = -M.lp(-(PH[a] - PH[b])).fun
    nec = np.array([[a != b and dmax[b, a] <= 1e-12 for b in range(nC)] for a in range(nC)])
    pw = []
    for i in range(nC):
        rows = np.array([np.append(-(PH[i] - PH[k]), 1.0) for k in range(nC) if k != i])
        pw.append(-M.lp(np.append(np.zeros(M.n), -1.0), rows, np.zeros(len(rows)), nvar_extra=1).fun)
    regret = dmax.max(0)
    th = M.sample_theta(10000, rng)
    U = noisy_U(M, th)
    r = ranks(U)
    U0 = PH @ M.theta0
    t = pd.DataFrame({"city": CITY, "U_ref": U0, "rank_ref": ranks(U0), "necessarily_beats": nec.sum(1), "necessarily_beaten_by": nec.sum(0),
                      "possible_winner_margin": pw, "max_regret": regret, "smaa_p_first": (r == 1).mean(0),
                      "smaa_p_top3": (r <= 3).mean(0), "smaa_mean_rank": r.mean(0)}, index=CID)
    return t.sort_values("rank_ref"), nec, th


# ---------------------------------------------------------------- 1. Theta_PLAN
MP = Model(SPEC_M2, STATEMENTS_PLAN)
OUT["theta0_satisfies_statements"] = MP.feasible(MP.theta0)
tP, necP, thP = robust(MP, "plan")
tP.round(4).to_csv(RES / "M2_plan_preferences_robust.csv")
nec_list = [(CITY[a], CITY[b]) for a in range(nC) for b in range(nC) if necP[a, b]]
pd.DataFrame(nec_list, columns=["necessarily_at_least_as_good", "than"]).to_csv(RES / "M2_plan_preferences_necessary_pairs.csv", index=False)
OUT["plan_statements"] = [{k: v for k, v in s.items()} for s in STATEMENTS_PLAN]
OUT["plan"] = {"necessary_pairs": len(nec_list), "possible_winners": tP.city[tP.possible_winner_margin >= 0].tolist(),
               "min_regret_city": tP.city[tP.max_regret.idxmin()], "min_regret": round(float(tP.max_regret.min()), 4),
               "smaa_p_first": tP.sort_values("smaa_p_first", ascending=False).head(5).set_index("city").smaa_p_first.round(4).to_dict(),
               "never_possible_winners": tP.city[tP.possible_winner_margin < 0].tolist()}

# leave one statement out (does any single statement drive the conclusion?)
loo = []
for st in STATEMENTS_PLAN:
    m = Model(SPEC_M2, [s for s in STATEMENTS_PLAN if s is not st])
    t, nec, _ = robust(m, st["id"])
    top = t.sort_values("smaa_p_first", ascending=False).head(3)
    loo.append({"removed": st["id"], "necessary_pairs": int(nec.sum()), "possible_winners": int((t.possible_winner_margin >= 0).sum()),
                "min_regret_city": t.city[t.max_regret.idxmin()],
                "smaa_top3": "; ".join(f"{c} {p:.3f}" for c, p in zip(top.city, top.smaa_p_first))})
pd.DataFrame(loo).set_index("removed").to_csv(RES / "M2_plan_preferences_leave_one_statement_out.csv")
OUT["plan_leave_one_statement_out"] = loo

# ---------------------------------------------------------------- 2. ELECTRE III with weights and value shapes sampled from Theta
M = Model(SPEC_M2)
PH = M.phi(fill_missing(X[M.inds]).values)
q, p, v = 0.05, 0.20, 0.80
rows = []
for label, model, ths in (("broad", M, M.sample_theta(400, rng)), ("plan", MP, thP[:400])):
    kern = np.zeros(nC); pos = np.zeros(nC)
    for th in ths:
        w = th.reshape(M.m, 3).sum(1)
        val = (PH * th).reshape(nC, M.m, 3).sum(2) / w
        sig, _ = electre(val, w, q, p, v)
        rk, inc = final_order(distill(sig, True), distill(sig, False))
        kern += rk == 1; pos += rk
    for i in range(nC):
        rows.append({"set": label, "city": CITY[i], "p_in_kernel": kern[i] / len(ths), "mean_cities_above_plus1": pos[i] / len(ths)})
se = pd.DataFrame(rows).pivot(index="city", columns="set")
se.columns = [f"{a}_{b}" for a, b in se.columns]
se = se.sort_values("p_in_kernel_broad", ascending=False)
se.round(4).to_csv(RES / "M2_electre_sampled_weights.csv")
OUT["electre_sampled_weights_p_in_kernel"] = {c: se[c].head(5).round(3).to_dict() for c in ("p_in_kernel_broad", "p_in_kernel_plan")}

json.dump(OUT, open(RES / "preferences_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(OUT, indent=1, ensure_ascii=False, default=float))
