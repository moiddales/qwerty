"""Remaining robustness computations on the final model M2 under Theta_PLAN.

1. Exact robust preference under 90% data intervals (continuous data uncertainty).
2. Regret on a squared utility scale (scale dependence of minimax regret).
3. Safety measured with the Poisson-Gamma teen traffic death rate.
4. Lower-tail share alpha = 0.1 / 0.2 / 0.3 for transit accessibility.
5. Correlated versus independent measurement errors in SMAA.

    cd projects/himcm2026A/analysis/model && python run_robustness.py
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from core import Model, SPEC_M2, STATEMENTS_PLAN, DOMAINS, RES, load, fill_missing, ranks

rng = np.random.default_rng(99)
names, X, S = load()
CITY, CID, nC = names.values, names.index, len(names)
MP = Model(SPEC_M2, STATEMENTS_PLAN)
Xr = fill_missing(X[MP.inds])
PH = MP.phi(Xr.values)
U0 = PH @ MP.theta0
OUT = {}

# ---------------------------------------------------------------- 1. robust preference under data intervals
# phi is non-decreasing in "goodness" for every indicator and theta >= 0, so for every theta the worst case of
# U_a - U_b over the data box puts a at the bad end and b at the good end of its 90% interval. The minimum over
# theta and data is therefore one LP with these two fixed phi rows: exact, not sampled.
z = 1.645
good_dir = np.sign(MP.nodes[:, 3] - MP.nodes[:, 0])
sd = S[MP.inds].values
lo_x = Xr.values - z * sd * good_dir           # bad end
hi_x = Xr.values + z * sd * good_dir           # good end
PH_lo, PH_hi = MP.phi(lo_x), MP.phi(hi_x)
nec = np.zeros((nC, nC), bool)
for a in range(nC):
    for b in range(nC):
        if a != b:
            nec[a, b] = MP.lp(PH_lo[a] - PH_hi[b]).fun >= 0
pairs = [(CITY[a], CITY[b]) for a in range(nC) for b in range(nC) if nec[a, b]]
pd.DataFrame(pairs, columns=["necessarily_at_least_as_good_under_90pct_intervals", "than"]).to_csv(RES / "M2_plan_robust_data_intervals.csv", index=False)
OUT["robust_under_data_intervals"] = {"necessary_pairs": len(pairs), "pairs": pairs}

# ---------------------------------------------------------------- 2. regret on squared utilities (sampled over Theta_PLAN)
th = MP.sample_theta(4000, rng)
U = PH @ th.T                                      # cities x samples
reg_lin = (U.max(0)[None] - U).max(1)
reg_sq = ((U ** 2).max(0)[None] - U ** 2).max(1)
OUT["regret_scale"] = {"min_regret_linear": CITY[reg_lin.argmin()], "min_regret_squared": CITY[reg_sq.argmin()],
                       "top3_linear": CITY[np.argsort(reg_lin)[:3]].tolist(), "top3_squared": CITY[np.argsort(reg_sq)[:3]].tolist()}

# ---------------------------------------------------------------- 3. safety with the Poisson-Gamma teen rate
pg = pd.read_csv(RES / "poisson_gamma_teen_traffic.csv", dtype={"city_id": str}, index_col=0).reindex(CID)
spec = {k: v for k, v in SPEC_M2.items() if k != "S2_traffic_deaths"}
spec["S2r_teen_traffic_eb"] = ("Safety", [12, 8, 5, 2], "Poisson-Gamma posterior traffic deaths at ages 14-18 per 100,000")
Xp = X.copy(); Xp["S2r_teen_traffic_eb"] = pg.eb_per_100k.values
mp = Model(spec, STATEMENTS_PLAN)
u = mp.phi(fill_missing(Xp[mp.inds]).values) @ mp.theta0
OUT["safety_teen_traffic_eb"] = {"champion": CITY[u.argmax()], "top5": CITY[np.argsort(-u)[:5]].tolist(),
                                 "kendall_tau_vs_M2": round(stats.kendalltau(U0, u)[0], 3)}

# ---------------------------------------------------------------- 4. lower-tail share alpha
bg = pd.read_csv(RES / "sld_block_groups.csv", dtype={"city_id": str})


def lower_tail(v, w, alpha):
    o = np.argsort(v); v, w = v[o], w[o] / w.sum()
    take = np.clip(alpha - (np.cumsum(w) - w), 0, w)
    return (v * take).sum() / alpha


lt = pd.DataFrame({a: bg.groupby("city_id").apply(lambda g: lower_tail(g.D5BR0.values / 1000, g.TotPop.values, a), include_groups=False)
                   for a in (0.1, 0.2, 0.3)}).reindex(CID)
lt.index = CITY
rk = lt.rank(ascending=False)
lt.round(2).assign(**{f"rank_{a}": rk[a] for a in lt.columns}).to_csv(RES / "access_lower_tail_alpha.csv")
OUT["lower_tail_alpha"] = {"spearman_0.1_vs_0.3": round(stats.spearmanr(lt[0.1], lt[0.3])[0], 3),
                           "max_rank_change_0.1_to_0.3": int((rk[0.1] - rk[0.3]).abs().max())}

# ---------------------------------------------------------------- 5. correlated vs independent errors
n = 5000
th = MP.sample_theta(n, rng)
x, s = Xr.values, S[MP.inds].values
dom_idx = np.array([DOMAINS.index(d) for d in MP.dom])
res = {}
for label in ("independent", "common_within_domain"):
    pf = np.zeros(nC)
    for a in range(0, n, 500):
        k = min(500, n - a)
        if label == "independent":
            e = rng.standard_normal((k, nC, MP.m))
        else:                                   # one shock per city and domain, shared by its indicators
            e = rng.standard_normal((k, nC, len(DOMAINS)))[:, :, dom_idx]
        d = x[None] + e * s[None] * good_dir[None, None]
        uu = np.einsum("nck,nk->nc", MP.phi(d.reshape(-1, MP.m)).reshape(k, nC, MP.n), th[a:a + k])
        pf += np.bincount(uu.argmax(1), minlength=nC)
    res[label] = {CITY[i]: round(pf[i] / n, 3) for i in np.argsort(-pf)[:4]}
OUT["error_correlation_p_first"] = res

json.dump(OUT, open(RES / "robustness_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(OUT, indent=1, ensure_ascii=False, default=float))
