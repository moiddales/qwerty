"""Full model computation on the real 25-city indicator matrix.

    python projects/himcm2026A/analysis/model/build_matrix.py
    python projects/himcm2026A/analysis/model/run_model.py

Writes CSV tables and summary.json to projects/himcm2026A/results/.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from core import (Model, SPEC_M0, SPEC_M1, SPEC_M2, DOMAINS, FLOORS, REF_INCOME, RES, load, fill_missing, ranks)

N_SMAA = 10000
rng = np.random.default_rng(20261111)
names, X_all, S_all = load()
CITY = names.values
CID = names.index
nC = len(CITY)
SUM = {}


def tab(df, name):
    df.to_csv(RES / f"{name}.csv")
    return df


def eligible_mask(Xv):
    """Xv: DataFrame or dict of arrays with floor indicators. True = passes all reference floors."""
    ok = np.ones(np.shape(Xv["C1_rent_share"]), bool)
    for k, f in FLOORS.items():
        ok &= np.asarray(Xv[k]) <= f
    return ok


def dom_totals(model, th):
    th = np.atleast_2d(th)
    per_ind = th.reshape(len(th), model.m, 3).sum(2)
    return pd.DataFrame({d: per_ind[:, [j for j in range(model.m) if model.dom[j] == d]].sum(1) for d in DOMAINS})


def draw_data(model, X, S, n):
    """n noisy copies of the raw matrix; a missing value is drawn from the cities that have data."""
    x = X[model.inds].values.astype(float)
    s = S[model.inds].values.astype(float)
    out = x[None] + rng.standard_normal((n,) + x.shape) * s[None]
    for j in range(model.m):
        miss = np.isnan(x[:, j])
        if miss.any():
            pool = x[~miss, j]
            out[:, miss, j] = rng.choice(pool, size=(n, miss.sum()))
    return out


def smaa(model, X, S, thetas, noise=True, floors=None):
    n = len(thetas)
    data = draw_data(model, X, S, n) if noise else np.repeat(fill_missing(X[model.inds]).values[None], n, 0)
    U = np.vstack([np.einsum("nck,nk->nc", model.phi(data[a:a + 500].reshape(-1, model.m)).reshape(-1, nC, model.n), thetas[a:a + 500])
                   for a in range(0, n, 500)])
    out = {"U": U, "rank": ranks(U)}
    if floors is not None:
        idx = {k: model.inds.index(k) for k in FLOORS if k in model.inds}
        elig = np.ones((n, nC), bool)
        for k, j in idx.items():
            elig &= data[:, :, j] <= FLOORS[k]
        Ue = np.where(elig, U, -np.inf)
        first = Ue.argmax(1)
        out.update(elig=elig, first_elig=first, any_elig=elig.any(1))
    return out


def smaa_table(res):
    r = res["rank"]
    acc = np.stack([(r == k).mean(0) for k in range(1, nC + 1)], 1)
    t = pd.DataFrame({"city": CITY, "p_first": acc[:, 0], "p_top3": acc[:, :3].sum(1), "p_top10": acc[:, :10].sum(1),
                      "mean_rank": r.mean(0), "rank_p05": np.percentile(r, 5, 0), "rank_p95": np.percentile(r, 95, 0)}, index=CID)
    return t, acc


def analyse(tag, spec, X, S):
    M = Model(spec)
    assert M.feasible(M.theta0)
    Xr = fill_missing(X[M.inds])
    PH = M.phi(Xr.values)
    U0 = PH @ M.theta0
    order = np.argsort(-U0)
    # ---- reference ranking with domain contributions and missing-value range
    contrib = (PH * M.theta0).reshape(nC, M.m, 3).sum(2)
    ref = pd.DataFrame({"city": CITY, "U_ref": U0, "rank_ref": ranks(U0)}, index=CID)
    for d in DOMAINS:
        ref[d] = contrib[:, [j for j in range(M.m) if M.dom[j] == d]].sum(1)
    lo_fill, hi_fill = X[M.inds].copy(), X[M.inds].copy()
    for j, c in enumerate(M.inds):
        lo_fill[c] = lo_fill[c].fillna(M.nodes[j, 0]); hi_fill[c] = hi_fill[c].fillna(M.nodes[j, 3])
    U_lo, U_hi = M.phi(lo_fill.values) @ M.theta0, M.phi(hi_fill.values) @ M.theta0
    ref["missing"] = X[M.inds].isna().apply(lambda r: ";".join(r.index[r]), axis=1)
    # rank range of a city with missing data: its own value at worst/best, everyone else at reference
    ref["rank_if_missing_worst"] = [int((U0 > U_lo[i]).sum() - (U0[i] > U_lo[i]) + 1) for i in range(nC)]
    ref["rank_if_missing_best"] = [int((U0 > U_hi[i]).sum() + 1) for i in range(nC)]
    ref["eligible_point"] = eligible_mask(X)
    tab(ref.sort_values("rank_ref").round(4), f"{tag}_reference_ranking")

    # ---- Pareto dominance on partial values (indicator level)
    z = PH.reshape(nC, M.m, 3).sum(2)
    dominated_by = {CITY[i]: [CITY[k] for k in range(nC) if k != i and np.all(z[k] >= z[i]) and np.any(z[k] > z[i])] for i in range(nC)}

    # ---- robust preference: pairwise LP bounds
    dmin = np.zeros((nC, nC)); dmax = np.zeros((nC, nC))
    for a in range(nC):
        for b in range(a + 1, nC):
            c = PH[a] - PH[b]
            lo = M.lp(c).fun; hi = -M.lp(-c).fun
            dmin[a, b], dmax[a, b] = lo, hi
            dmin[b, a], dmax[b, a] = -hi, -lo
    tab(pd.DataFrame(dmin, CITY, CITY).round(4), f"{tag}_pairwise_min_difference")
    tab(pd.DataFrame(dmax, CITY, CITY).round(4), f"{tag}_pairwise_max_difference")
    necessary = (dmin >= 0) & ~np.eye(nC, dtype=bool)
    # ---- possible winner: max margin s with (phi_i - phi_k) theta >= s for all k
    pw = []
    for i in range(nC):
        rows = np.array([np.append(-(PH[i] - PH[k]), 1.0) for k in range(nC) if k != i])
        r = M.lp(np.append(np.zeros(M.n), -1.0), rows, np.zeros(len(rows)), nvar_extra=1)
        pw.append(-r.fun)
    regret = dmax.max(axis=0)                     # R_i = max_k max_theta (U_k - U_i)
    rob = pd.DataFrame({"city": CITY, "rank_ref": ranks(U0), "necessarily_beats": necessary.sum(1),
                        "necessarily_beaten_by": necessary.sum(0), "possible_winner_margin": pw,
                        "max_regret": regret, "regret_rank": ranks(-regret),
                        "worst_rival": [CITY[k] for k in dmax.argmax(axis=0)]}, index=CID)
    tab(rob.sort_values("rank_ref").round(4), f"{tag}_robust_preference")

    # ---- champion as one domain's total varies (others rescaled proportionally)
    sw = []
    dt0 = dom_totals(M, M.theta0).iloc[0]
    for d in DOMAINS:
        in_d = np.repeat([x == d for x in M.dom], 3)
        prev = None
        for t in np.arange(0, 0.6001, 0.0025):
            th = np.where(in_d, M.theta0 * t / dt0[d], M.theta0 * (1 - t) / (1 - dt0[d]))
            w = CITY[np.argmax(PH @ th)]
            if w != prev:
                sw.append({"domain": d, "from_share": round(t, 4), "champion": w})
                prev = w
    tab(pd.DataFrame(sw), f"{tag}_champion_by_domain_share")

    # ---- SMAA scenarios
    th_flat = M.sample_theta(N_SMAA, rng)
    eq = {d: 1 / 7 for d in DOMAINS}
    th_near = M.sample_theta(N_SMAA, rng, centre=eq, conc=200)
    scen = {"broad": smaa(M, X, S, th_flat, floors=True),
            "near_reference": smaa(M, X, S, th_near),
            "data_noise_only": smaa(M, X, S, np.repeat(M.theta0[None], N_SMAA, 0)),
            "preference_only": smaa(M, X, S, th_flat, noise=False)}
    for d in DOMAINS:
        prof = {k: (2 / 7 if k == d else (1 - 2 / 7) / 6) for k in DOMAINS}
        prof = {k: min(v, 0.2857) for k, v in prof.items()}
        scen[f"profile_{d}"] = smaa(M, X, S, M.sample_theta(N_SMAA, rng, centre=prof, conc=200))
    first = pd.DataFrame({"city": CITY}, index=CID)
    for k, res in scen.items():
        t, acc = smaa_table(res)
        first[k] = t.p_first
        if k == "broad":
            t["rank_ref"] = ranks(U0)
            tab(t.sort_values("mean_rank").round(4), f"{tag}_smaa_broad")
            tab(pd.DataFrame(acc, CITY, range(1, nC + 1)).round(4), f"{tag}_smaa_rank_acceptability")
            U = res["U"]
            pair = (U[:, :, None] > U[:, None, :]).mean(0)
            tab(pd.DataFrame(pair, CITY, CITY).round(4), f"{tag}_smaa_pairwise_win")
            # central weights and confidence factors
            cw = []
            for i in np.flatnonzero(t.p_first.values > 0.005):
                sel = res["rank"][:, i] == 1
                c = th_flat[sel].mean(0)
                conf = (smaa(M, X, S, np.repeat(c[None], 2000, 0))["rank"][:, i] == 1).mean()
                cw.append({"city": CITY[i], "p_first": sel.mean(), "confidence_factor": conf, **dom_totals(M, c).iloc[0].round(3).to_dict()})
            tab(pd.DataFrame(cw).sort_values("p_first", ascending=False).round(4), f"{tag}_smaa_central_weights")
            el = res["elig"]; fe = res["first_elig"]; ae = res["any_elig"]
            pf = np.array([(fe[ae] == i).sum() / len(fe) for i in range(nC)])
            et = pd.DataFrame({"city": CITY, "pass_rate": el.mean(0), "p_eligible_and_first": pf,
                               "p_first_given_eligible": pf / np.maximum(el.mean(0), 1e-12)}, index=CID)
            tab(et.sort_values("p_eligible_and_first", ascending=False).round(4), f"{tag}_smaa_eligibility")
    tab(first.sort_values("broad", ascending=False).round(4), f"{tag}_smaa_p_first_by_scenario")

    top = [CITY[i] for i in order[:10]]
    SUM[tag] = {"reference_top10": top, "champion": top[0], "champion_U": round(float(U0[order[0]]), 4),
                "gap_1_2": round(float(U0[order[0]] - U0[order[1]]), 4),
                "necessary_pairs": int(necessary.sum()), "pairs": nC * (nC - 1) // 2,
                "possible_winners": [CITY[i] for i in range(nC) if pw[i] >= 0],
                "min_regret_city": CITY[int(np.argmin(regret))], "min_regret": round(float(regret.min()), 4),
                "pareto_dominated": {k: v for k, v in dominated_by.items() if v},
                "smaa_broad_p_first_top5": first.sort_values("broad", ascending=False).head(5).set_index("city").broad.round(4).to_dict()}
    return M, PH, U0, th_flat


# =====================================================================================================
M0, PH0, U0, th0s = analyse("M0", SPEC_M0, X_all, S_all)
M1, PH1, U1, th1s = analyse("M1", SPEC_M1, X_all, S_all)
M2, PH2, U2, th2s = analyse("M2", SPEC_M2, X_all, S_all)

# ---------- revision comparison M0 -> M1 (and each change alone)
cmp = pd.DataFrame({"city": CITY, "rank_M0": ranks(U0), "rank_M1": ranks(U1), "rank_M2": ranks(U2), "U_M0": U0, "U_M1": U1, "U_M2": U2}, index=CID)
spec_a = {k: v for k, v in SPEC_M0.items() if k != "E2_grad_rate"}; spec_a["E2r_grad_district"] = SPEC_M1["E2r_grad_district"]
spec_b = {k: v for k, v in SPEC_M0.items() if k != "M1_transit_frequency"}
spec_b.update({k: SPEC_M1[k] for k in ("M1r_transit_hours_pc", "M4r_weekend_retention")})
for lab, sp in (("grad_only", spec_a), ("transit_only", spec_b)):
    m = Model(sp); cmp[f"rank_{lab}"] = ranks(m.phi(fill_missing(X_all[m.inds]).values) @ m.theta0)
cmp["shift"] = cmp.rank_M0 - cmp.rank_M1
tab(cmp.sort_values("rank_M2").round(4), "revision_M0_M1_M2")
SUM["revision"] = {"kendall_tau_M0_M1": round(stats.kendalltau(U0, U1)[0], 3), "kendall_tau_M1_M2": round(stats.kendalltau(U1, U2)[0], 3),
                   "moves_M1_to_M2": cmp[cmp.rank_M1 != cmp.rank_M2][["city", "rank_M1", "rank_M2"]].values.tolist(),
                   "spearman_access_vs_service_hours": round(stats.spearmanr(X_all.M5r_transit_access, X_all.M1r_transit_hours_pc)[0], 3),
                   "largest_moves": cmp.reindex(cmp["shift"].abs().sort_values(ascending=False).index).head(6)[["city", "rank_M0", "rank_M1"]].values.tolist(),
                   "sld_vs_ntd_spearman": round(stats.spearmanr(X_all.M1_transit_frequency, X_all.M1r_transit_hours_pc, nan_policy="omit")[0], 3)}

# =====================================================================================================
# The remaining analyses use the final model M2.
M, PH, U, X, S = M2, PH2, U2, X_all, S_all
Xr = fill_missing(X[M.inds])
ind_w = M.theta0.reshape(M.m, 3).sum(1)
z_lin = np.clip((Xr.values - M.nodes[:, 0]) / (M.nodes[:, 3] - M.nodes[:, 0]), 0, 1)   # linear 0-1 position between worst and best

# ---------- floors: three states, joint pass probability, scans
fl = pd.DataFrame({"city": CITY}, index=CID)
z90 = 1.645
pj = []
for k, f in FLOORS.items():
    x, s = X[k], S[k]
    fl[k] = x.round(2)
    fl[k + "_state"] = np.where(x + z90 * s <= f, "pass", np.where(x - z90 * s > f, "fail", "pending"))
    pj.append(stats.norm.cdf((f - x) / np.where(s > 0, s, 1e-9)))
pj = np.array(pj)
sim = draw_data(M, X, S, 20000).astype(np.float32)
simX = {k: (sim[:, :, M.inds.index(k)] if k in M.inds else np.repeat(X[k].values[None], 20000, 0)) for k in FLOORS}
simX["S1_violent_crime"] = X.S1_violent_crime.values + rng.standard_normal((20000, nC)) * S.S1_violent_crime.values
fl["p_joint_simulation"] = eligible_mask(simX).mean(0)
fl["p_joint_product"] = pj.prod(0)
fl["p_joint_bonferroni_lower"] = np.maximum(0, 1 - (1 - pj).sum(0))
fl["point_eligible"] = eligible_mask(X)
states = fl[[c for c in fl.columns if c.endswith("_state")]]
fl["status"] = np.where((states == "fail").any(axis=1), "fail", np.where((states == "pending").any(axis=1), "pending", "pass"))
tab(fl.round(4), "floors_status")
SUM["floors"] = {"reference_income": REF_INCOME, "thresholds": FLOORS,
                 "fail": fl[fl.status == "fail"].city.tolist(), "pending": fl[fl.status == "pending"].city.tolist(),
                 "max_gap_simulation_minus_bonferroni": round(float((fl.p_joint_simulation - fl.p_joint_bonferroni_lower).max()), 4)}

scan = []
for inc in (50000, 60000, 70000, 80000, 100000, 120000):
    _, Xi, _ = load(inc)
    ph = M.phi(fill_missing(Xi[M.inds]).values); u = ph @ M.theta0
    ok = eligible_mask(Xi)
    order = [i for i in np.argsort(-u) if ok[i]]
    scan.append({"scan": "income", "value": inc, "n_fail": int((~ok).sum()), "failing": ";".join(CITY[~ok]),
                 "champion_eligible": CITY[order[0]], "top5_eligible": ";".join(CITY[order[:5]])})
for k, grid in (("S1_violent_crime", [600, 700, 800, 900, 1000, 1100, 1200]), ("S2_traffic_deaths", [8, 10, 12, 14, 16, 18, 20]),
                ("H1_bad_air_days", [5, 10, 15, 20, 25, 30]), ("C1_rent_share", [30, 35, 40, 45, 50])):
    for f in grid:
        ok = eligible_mask(X) & (X[k].values <= f)
        order = [i for i in np.argsort(-U) if ok[i]]
        scan.append({"scan": k, "value": f, "n_fail": int((~ok).sum()), "failing": ";".join(CITY[~ok]),
                     "champion_eligible": CITY[order[0]] if order else "", "top5_eligible": ";".join(CITY[order[:5]])})
tab(pd.DataFrame(scan).set_index("scan"), "floors_scan")

# ---------- ELECTRE III on per-indicator partial values (concave theta0 shape, 0 = worst node, 1 = best node)
val = (PH * M.theta0).reshape(nC, M.m, 3).sum(2) / ind_w


def electre(val, q, p, v):
    d = val[None, :, :] - val[:, None, :]              # d[a,b,j] = g_j(b) - g_j(a)
    C = (np.clip((p - d) / (p - q), 0, 1) * ind_w).sum(2)
    dj = np.clip((d - p) / (v - p), 0, 1) if v < 1 else np.zeros_like(d)
    sig = C.copy()
    for a in range(nC):
        for b in range(nC):
            if a != b and C[a, b] < 1:
                k = dj[a, b] > C[a, b]
                sig[a, b] = C[a, b] * np.prod((1 - dj[a, b][k]) / (1 - C[a, b]))
    np.fill_diagonal(sig, 0)
    return sig, dj


def distill(sig, descending=True):
    """Standard ELECTRE III distillation with s(lambda) = 0.30 - 0.15 lambda. Returns class index (1 = best)."""
    s = lambda lam: 0.30 - 0.15 * lam
    left, classes = list(range(len(sig))), []
    while left:
        D = left[:]
        lam = sig[np.ix_(D, D)].max()
        while len(D) > 1 and lam > 0:
            sub = sig[np.ix_(D, D)]
            below = sub[(sub < lam - s(lam)) & ~np.eye(len(D), dtype=bool)]
            lam_next = below.max() if below.size else 0.0
            out = (sub > lam_next) & (sub - sub.T > s(sub))
            qual = out.sum(1) - out.sum(0)
            target = qual.max() if descending else qual.min()
            D = [D[i] for i in range(len(D)) if qual[i] == target]
            lam = lam_next
        classes.append(D)
        left = [x for x in left if x not in D]
    if not descending:
        classes = classes[::-1]
    r = np.zeros(len(sig), int)
    for k, cl in enumerate(classes):
        r[cl] = k + 1
    return r


def final_order(r1, r2):
    """Intersection of the two preorders: a above b if a is at least as good in both and better in one."""
    above = ((r1[:, None] <= r1[None, :]) & (r2[:, None] <= r2[None, :]) & ((r1[:, None] < r1[None, :]) | (r2[:, None] < r2[None, :])))
    incomparable = ~above & ~above.T & ~((r1[:, None] == r1[None, :]) & (r2[:, None] == r2[None, :]))
    return above.sum(0) + 1, incomparable.sum(1)


q, p, v = 0.05, 0.20, 0.80
sig, dj = electre(val, q, p, v)
r_desc, r_asc = distill(sig, True), distill(sig, False)
pos, inc = final_order(r_desc, r_asc)
el = pd.DataFrame({"city": CITY, "rank_additive": ranks(U), "electre_descending": r_desc, "electre_ascending": r_asc,
                   "cities_strictly_above": pos - 1, "incomparable_with": inc,
                   "electre_mean_position": (stats.rankdata(r_desc) + stats.rankdata(r_asc)) / 2,
                   "vetoed_against": [int((dj[a] >= 1).any(1).sum()) for a in range(nC)]}, index=CID)
tab(el.sort_values(["cities_strictly_above", "electre_mean_position"]), "electre_iii")
tab(pd.DataFrame(sig, CITY, CITY).round(3), "electre_credibility")
champ = int(np.argmax(U))
ev = {}
for vv in (0.6, 0.8, 1.0):
    for pp in (0.15, 0.20, 0.30):
        sg, _ = electre(val, q, pp, vv)
        rd, ra = distill(sg, True), distill(sg, False)
        top = el.city.values[np.flatnonzero(final_order(rd, ra)[0] == 1)].tolist()
        ev[f"p{pp}_v{vv}"] = top
SUM["electre"] = {"thresholds_q_p_v": [q, p, v],
                  "kernel_no_city_above": el.city[pos == 1].tolist(),
                  "top6_by_mean_position": el.sort_values("electre_mean_position").city.head(6).tolist(),
                  "spearman_vs_additive": round(stats.spearmanr(el.rank_additive, el.electre_mean_position)[0], 3),
                  "additive_champion_vetoed_against": [CITY[b] for b in range(nC) if (dj[champ, b] >= 1).any()],
                  "kernel_by_threshold": ev}

# ---------- structural contrasts: exponential value, CES across domains, Choquet, entropy / CRITIC
struct = pd.DataFrame({"city": CITY, "piecewise_ref": ranks(U)}, index=CID)
for k in (1, 2, 4):
    struct[f"exp_k{k}"] = ranks(((1 - np.exp(-k * z_lin)) / (1 - np.exp(-k)) * ind_w).sum(1))
struct["linear"] = ranks((z_lin * ind_w).sum(1))
contrib = (PH * M.theta0).reshape(nC, M.m, 3).sum(2)
dom_score = np.stack([contrib[:, [j for j in range(M.m) if M.dom[j] == dname]].sum(1) * 7 for dname in DOMAINS], 1)   # 0-1 per domain
ces = lambda rho: np.exp(np.log(dom_score).mean(1)) if rho == 0 else ((dom_score ** rho).mean(1)) ** (1 / rho)
for rho in (0.5, 0, -1, -2, -5):
    struct[f"ces_rho{rho}"] = ranks(ces(rho))
prev, ces_sw = None, []
for rho in np.round(np.arange(1, -10.01, -0.05), 2):
    w = CITY[np.argmax(ces(rho))]
    if w != prev:
        ces_sw.append([float(rho), w]); prev = w
iM, iA = DOMAINS.index("Mobility"), DOMAINS.index("Activities")
for I in (0.05, 0.10):                                 # 2-additive Choquet: Mobility and Activities complementary
    struct[f"choquet_MA_{I}"] = ranks(dom_score.mean(1) - 0.5 * I * np.abs(dom_score[:, iM] - dom_score[:, iA]))
raw = Xr.values; sign = np.sign(M.nodes[:, 3] - M.nodes[:, 0])
mm = (raw - raw.min(0)) / (raw.max(0) - raw.min(0)); mm = np.where(sign > 0, mm, 1 - mm)
pr = (mm + 1e-9) / (mm + 1e-9).sum(0)
ent = 1 + (pr * np.log(pr)).sum(0) / np.log(nC); w_ent = ent / ent.sum()
corr = np.corrcoef(mm.T); w_cr = mm.std(0, ddof=1) * (1 - corr).sum(0); w_cr /= w_cr.sum()
struct["entropy_minmax"] = ranks(mm @ w_ent); struct["critic_minmax"] = ranks(mm @ w_cr)
tab(struct.sort_values("piecewise_ref"), "structure_contrasts")
tab(pd.DataFrame({"indicator": M.inds, "reference_theta0": ind_w, "entropy": w_ent, "critic": w_cr}).round(4).set_index("indicator"), "weights_reference_vs_data_driven")


def loo_reversals(score_fn):
    """Pairs of cities whose order changes when one other city is removed from the candidate set."""
    base = score_fn(np.arange(nC)); n = 0
    for drop in range(nC):
        keep = np.array([i for i in range(nC) if i != drop]); u = score_fn(keep)
        b = base[keep]
        n += int(((b[:, None] > b[None, :]) & (u[:, None] < u[None, :])).sum())
    return n


def ent_score(keep):
    r = raw[keep]; m2 = (r - r.min(0)) / (r.max(0) - r.min(0)); m2 = np.where(sign > 0, m2, 1 - m2)
    p2 = (m2 + 1e-9) / (m2 + 1e-9).sum(0); e2 = 1 + (p2 * np.log(p2)).sum(0) / np.log(len(keep))
    return m2 @ (e2 / e2.sum())


SUM["structure"] = {"kendall_tau_vs_reference": {c: round(stats.kendalltau(struct.piecewise_ref, struct[c])[0], 3) for c in struct.columns[2:]},
                    "champion_by_column": {c: struct.city[struct[c] == 1].iloc[0] for c in struct.columns[1:]},
                    "ces_champion_switches_rho": ces_sw,
                    "entropy_top_weights": dict(sorted(zip(M.inds, w_ent.round(3)), key=lambda t: -t[1])[:4]),
                    "leave_one_city_out_pair_reversals": {"fixed_reference_scale": loo_reversals(lambda keep: U[keep]),
                                                          "entropy_minmax": loo_reversals(ent_score)}}

# ---------- leave-one-indicator-out and node / noise sensitivity
loo = []
for j, ind in enumerate(M.inds):
    th = M.theta0.copy(); th[3 * j:3 * j + 3] = 0; th /= th.sum()
    u = PH @ th
    loo.append({"dropped": ind, "champion": CITY[np.argmax(u)], "kendall_tau": stats.kendalltau(U, u)[0],
                "top5": ";".join(CITY[np.argsort(-u)[:5]])})
tab(pd.DataFrame(loo).round(3).set_index("dropped"), "sensitivity_leave_one_indicator_out")
node_runs = []
for trial in range(2000):
    sp = {}
    for kname, (dm, nd, why) in M.spec.items():
        nd = np.array(nd, float); span = nd[3] - nd[0]
        nd2 = nd + np.array([1, 1, 1, 1]) * 0 + rng.uniform(-0.1, 0.1, 4) * span
        nd2 = np.sort(nd2) if span > 0 else -np.sort(-nd2)
        sp[kname] = (dm, list(nd2), why)
    m2 = Model(sp); u = m2.phi(Xr.values) @ m2.theta0
    node_runs.append(ranks(u))
node_runs = np.array(node_runs)
tab(pd.DataFrame({"city": CITY, "rank_ref": ranks(U), "p_first": (node_runs == 1).mean(0), "rank_p05": np.percentile(node_runs, 5, 0),
                  "rank_p95": np.percentile(node_runs, 95, 0)}, index=CID).sort_values("rank_ref").round(3), "sensitivity_reference_nodes")
noise = {}
for mult in (0.5, 1, 2, 4):
    r = smaa(M, X, S * mult, np.repeat(M.theta0[None], 5000, 0))["rank"]
    noise[str(mult)] = {CITY[i]: round(float((r[:, i] == 1).mean()), 3) for i in np.argsort(-(r == 1).mean(0))[:3]}
SUM["sensitivity"] = {"node_shift_10pct_p_first": {CITY[i]: round(float((node_runs[:, i] == 1).mean()), 3) for i in np.argsort(-(node_runs == 1).mean(0))[:4]},
                      "measurement_sd_multiplier_p_first": noise,
                      "leave_one_indicator_champions": pd.DataFrame(loo).champion.value_counts().to_dict()}

# ---------- hierarchical Poisson-Gamma for traffic deaths at ages 14-18
tc = pd.read_csv(RES / "teen_traffic_counts.csv", dtype={0: str}, index_col=0).reindex(CID)
Y, E = tc.deaths_14_18_2021_2024.values, tc.person_years_14_18.values
lam = Y.sum() / E.sum()
chi2 = ((Y - E * lam) ** 2 / (E * lam)).sum(); p_over = 1 - stats.chi2.cdf(chi2, nC - 1)
rate = Y / E
var_between = max(((E * (rate - lam) ** 2).sum() / E.sum()) - lam / E.mean(), 0)    # Marshall method of moments
pg = pd.DataFrame({"city": CITY, "deaths": Y, "person_years": E.round(0), "raw_per_100k": rate * 1e5}, index=CID)
if var_between > 0:
    a, b = lam ** 2 / var_between, lam / var_between
    pg["eb_per_100k"] = (a + Y) / (b + E) * 1e5
    pg["eb_lo90"] = stats.gamma.ppf(0.05, a + Y, scale=1 / (b + E)) * 1e5
    pg["eb_hi90"] = stats.gamma.ppf(0.95, a + Y, scale=1 / (b + E)) * 1e5
    pg["shrink_weight_on_own_data"] = E / (b + E)
    SUM["poisson_gamma"] = {"pooled_rate_per_100k": round(lam * 1e5, 2), "chi2": round(chi2, 1), "df": nC - 1, "p": float(f"{p_over:.3g}"),
                            "a": round(a, 2), "b": round(b, 0),
                            "spearman_eb_teen_vs_all_age_rate": round(stats.spearmanr(pg.eb_per_100k, X.S2_traffic_deaths)[0], 3)}
else:
    SUM["poisson_gamma"] = {"pooled_rate_per_100k": round(lam * 1e5, 2), "chi2": round(chi2, 1), "p": float(f"{p_over:.3g}"), "overdispersion": False}
tab(pg.round(3), "poisson_gamma_teen_traffic")

# ---------- distribution inside cities: transit service and walkability by block group
bgf = pd.read_csv(RES / "sld_block_groups.csv", dtype={"city_id": str})
cov = pd.read_csv(RES / "audit_sld_transit_coverage.csv", dtype={"city_id": str}).set_index("city_id")


def lower_tail_mean(v, w, alpha=0.2):
    o = np.argsort(v); v, w = v[o], w[o] / w.sum()
    cum = np.cumsum(w); take = np.clip(alpha - (cum - w), 0, w)
    return (v * take).sum() / alpha


rows = []
for c, g in bgf.groupby("city_id"):
    w = g.TotPop.values; f = g.D4C0.values; wk = g.NatWalkInd.values; ac = g.D5BR0.values / 1000
    rows.append({"city_id": c, "transit_mean": np.average(f, weights=w), "transit_lower20_mean": lower_tail_mean(f, w),
                 "pop_share_freq_ge_4_per_hour": np.average(f >= 4, weights=w), "pop_share_no_service": np.average(f <= 0, weights=w),
                 "walk_mean": np.average(wk, weights=w), "walk_lower20_mean": lower_tail_mean(wk, w),
                 "pop_share_walk_most_walkable": np.average(wk >= 15.26, weights=w),
                 "access_mean_kjobs": np.average(ac, weights=w), "access_lower20_mean_kjobs": lower_tail_mean(ac, w),
                 "pop_share_access_ge_60k": np.average(ac >= 60, weights=w), "pop_share_no_transit_access": np.average(ac <= 0, weights=w)})
eq = pd.DataFrame(rows).set_index("city_id").reindex(CID)
eq.insert(0, "city", CITY)
bad = cov.index[cov.pop_share_no_frequency_D4c - cov.pop_share_no_stop_within_1200m_D4a > 0.25]
eq.loc[bad, ["transit_mean", "transit_lower20_mean", "pop_share_freq_ge_4_per_hour", "pop_share_no_service"]] = np.nan
obs = pd.read_csv(RES.parent / "data/processed/observations_all_levels.csv.gz", dtype=str, low_memory=False)
obs["v"] = pd.to_numeric(obs.value, errors="coerce")
rb = obs[(obs.source_id == "S02") & (obs.indicator_id == "rent_burden_ge50_pct") & (obs.observation_period == "2020-2024")].set_index("city_id").v
eq["renters_paying_50pct_plus_acs"] = rb.reindex(CID)
tab(eq.round(3), "equity_within_city")
valid = eq.transit_mean.notna()
eq["rank_access_mean"] = ranks(eq.access_mean_kjobs.values); eq["rank_access_lower20"] = ranks(eq.access_lower20_mean_kjobs.values)
tab(eq.round(3), "equity_within_city")
SUM["equity"] = {"access_rank_moves_mean_vs_lower20": eq[(eq.rank_access_mean - eq.rank_access_lower20).abs() >= 3][["city", "rank_access_mean", "rank_access_lower20"]].values.tolist(),
                 "pop_share_no_transit_access_top": eq.sort_values("pop_share_no_transit_access", ascending=False).head(5).set_index("city").pop_share_no_transit_access.round(3).to_dict(),"spearman_transit_mean_vs_lower20": round(stats.spearmanr(eq.transit_mean[valid], eq.transit_lower20_mean[valid])[0], 3),
                 "spearman_transit_mean_vs_share_ge4": round(stats.spearmanr(eq.transit_mean[valid], eq.pop_share_freq_ge_4_per_hour[valid])[0], 3),
                 "cities_lower20_mean_zero": eq.city[valid & (eq.transit_lower20_mean <= 0)].tolist(),
                 "spearman_C1_rent_vs_acs_severe_burden": round(stats.spearmanr(X.C1_rent_2br, eq.renters_paying_50pct_plus_acs)[0], 3)}

# ---------- external checks (not used in model construction)
val = {}
oa = pd.read_csv(RES.parent / "data/extracted/foundation/opportunity/city_county_historical_outcomes.csv", dtype=str)
oa["w"] = oa.city_population_share_2025.astype(float); oa["k"] = pd.to_numeric(oa.kfr_pooled_pooled_p25, errors="coerce")
kfr = ((oa.k * oa.w).groupby(oa.city_id).sum() / oa.w.groupby(oa.city_id).sum()).reindex(CID)
val["opportunity_atlas_upward_mobility_vs_U"] = {"n": int(kfr.notna().sum()), "spearman": round(stats.spearmanr(kfr, U, nan_policy="omit")[0], 3)}
y = obs[(obs.source_id == "S12") & (obs.observation_period == "2023")]
yv = y.pivot_table(index="city_id", columns="indicator_id", values="v", aggfunc="first").reindex(CID)
dscore = pd.DataFrame(dom_score, CID, DOMAINS)
for code, target, lab in (("H13", -X.S1_violent_crime, "felt_unsafe_at_or_to_school_vs_violent_crime(expected -)"),
                          ("H75", X.A3_school_sports, "not_on_sports_team_vs_school_sports(expected -)"),
                          ("H26", dscore.Health, "felt_sad_or_hopeless_vs_health_domain(expected -)"),
                          ("H23", dscore.Inclusion, "bullied_at_school_vs_inclusion_domain(expected -)")):
    if code in yv:
        ok = yv[code].notna() & target.notna()
        val["yrbs2023_" + lab] = {"n": int(ok.sum()), "spearman": round(stats.spearmanr(yv[code][ok], target[ok])[0], 3)}
SUM["external_checks"] = val
tab(pd.concat([pd.Series(CITY, CID, name="city"), kfr.rename("opportunity_atlas_kfr_p25"), yv[[c for c in ("H13", "H75", "H26", "H23") if c in yv]]], axis=1).round(3), "external_check_values")

json.dump(SUM, open(RES / "summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(SUM, indent=1, ensure_ascii=False, default=float))
