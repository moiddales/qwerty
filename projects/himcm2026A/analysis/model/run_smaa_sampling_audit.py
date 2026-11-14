"""Audit of the Section 5.6 SMAA weight sampler (Model.sample_theta in core.py).

    cd projects/himcm2026A/analysis/model && python run_smaa_sampling_audit.py   # -> results/smaa_sampling_audit.json

Checks
  A. Reproduction: the Table 1 draw (seed 42) gives the published SMAA values.
  B. Feasibility: every accepted vector lies in Theta_S.
  C. The final rejection step (statements P1-P6 on the assembled vector) depends on the domain weights only,
     so it cannot distort the measure-share or segment levels and keeps the domain weights uniform on their region.
  D. Uniformity of each level, tested against an independent sampler (hit-and-run, uniform on the same polytope).
  E. Independence between levels.
  F. How the stated preferences move the domain-weight marginals (Theta vs Theta_S).
  G. Monte Carlo spread of Seattle's first-place share over five further seeds.
  H. Design sensitivity: SMAA with vectors drawn uniformly over the whole 60-dimensional Theta_S instead of level by level.
Nothing here changes the model or the published result files.
"""
import json
import numpy as np
import pandas as pd
from scipy import stats
from core import Model, SPEC_M2, STATEMENTS_PLAN, DOMAINS, DOM_LO, DOM_HI, LAST_SEG_MIN, RES, load, fill_missing, ranks

names, X, S = load()
CITY, nC = names.values, len(names)
MP = Model(SPEC_M2, STATEMENTS_PLAN)
SEA = list(CITY).index("Seattle")
OUT = {}


def noisy_U(M, thetas, rng):
    """Same computation as run_preferences.noisy_U, with the generator passed in."""
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


def smaa(th, rng):
    r = ranks(noisy_U(MP, th, rng))
    return r


def summary(r, top=4):
    p1 = (r == 1).mean(0); mr = r.mean(0)
    o = np.argsort(mr)[:top]
    return {CITY[i]: {"p_first": round(float(p1[i]), 4), "p_top3": round(float((r[:, i] <= 3).mean()), 4),
                      "mean_rank": round(float(mr[i]), 3)} for i in o}


def domain_weights(M, th):
    w = th.reshape(len(th), M.m, 3).sum(2)
    return np.stack([w[:, [j for j in range(M.m) if M.dom[j] == d]].sum(1) for d in DOMAINS], 1)


# ---------------------------------------------------------------- A. reproduction of Table 1
rng = np.random.default_rng(42)              # run_preferences draws the Table 1 vectors first from this generator
thP = MP.sample_theta(10000, rng)
rP = ranks(noisy_U(MP, thP, rng))
pub = pd.read_csv(RES / "M2_plan_preferences_robust.csv").set_index("city")
p1 = pd.Series((rP == 1).mean(0), index=CITY); mr = pd.Series(rP.mean(0), index=CITY)
OUT["A_reproduction"] = {"max_abs_diff_p_first": float((p1 - pub.smaa_p_first.reindex(CITY).values).abs().max()),
                         "max_abs_diff_mean_rank": float((mr - pub.smaa_mean_rank.reindex(CITY).values).abs().max()),
                         "seattle_p_first": round(float(p1["Seattle"]), 4)}

# ---------------------------------------------------------------- B. feasibility
OUT["B_all_accepted_feasible"] = bool(all(MP.feasible(t) for t in thP))

# ---------------------------------------------------------------- C. what the final rejection step depends on
only_p5 = Model(SPEC_M2, [s for s in STATEMENTS_PLAN if s["id"] == "P5"])      # same sampler, final check only on P5 rows
cand = only_p5.sample_theta(200000, np.random.default_rng(11))
W = domain_weights(MP, cand)
D = {d: k for k, d in enumerate(DOMAINS)}
w_rule = ((W[:, D["Education"]] >= W[:, D["Affordability"]]) & (W[:, D["Mobility"]] >= W[:, D["Affordability"]]) &
          (W[:, D["Mobility"]] >= 1 / 7) & (W[:, D["Education"]] >= 1 / 7) & (W[:, D["Safety"]] >= 1 / 7))
k = MP.n_statement_rows
theta_rule = np.all(cand @ MP.A_ub[-k:].T <= MP.b_ub[-k:] + 1e-12, axis=1)
# rows of statement P5 alone (the sampler already enforces P5 inside the measure-share level)
k5 = only_p5.n_statement_rows
p5_ok = np.all(cand @ only_p5.A_ub[-k5:].T <= only_p5.b_ub[-k5:] + 1e-12, axis=1)
OUT["C_final_rejection"] = {"candidates": len(cand), "P5_rows_rejected": int((~p5_ok).sum()),
                            "theta_check_equals_domain_weight_check": bool((w_rule == theta_rule).all()),
                            "accept_rate": round(float(theta_rule.mean()), 4)}


# ---------------------------------------------------------------- D. uniformity of each level against hit-and-run
def hit_and_run(A, b, x0, n, thin, burn, rng):
    """Uniform sampling of {x : A x <= b, sum x = 1} (x >= 0 must be among the rows) starting from interior x0."""
    x = x0.copy(); out = []; dim = len(x)
    for it in range(burn + n * thin):
        d = rng.standard_normal(dim); d -= d.mean(); d /= np.linalg.norm(d)
        Ad = A @ d; slack = b - A @ x
        with np.errstate(divide="ignore", invalid="ignore"):
            t = slack / Ad
        hi = t[Ad > 1e-15].min(); lo = t[Ad < -1e-15].max()
        x = x + rng.uniform(lo, hi) * d
        if it >= burn and (it - burn) % thin == 0:
            out.append(x.copy())
    return np.array(out)


def ks_table(a, b, labels):
    return {lab: {"ks_p": round(float(stats.ks_2samp(a[:, i], b[:, i]).pvalue), 3),
                  "mean_sampler": round(float(a[:, i].mean()), 4), "mean_hit_and_run": round(float(b[:, i].mean()), 4)}
            for i, lab in enumerate(labels)}


hr = np.random.default_rng(5)
# D1. domain weights: simplex, box [1/14, 2/7], P1-P4, P6
I7 = np.eye(7); rowsA = [-I7, -I7, I7]; rowsb = [np.zeros(7), -DOM_LO * np.ones(7), DOM_HI * np.ones(7)]
def ge(a, c):                                        # w_a >= w_c  ->  w_c - w_a <= 0
    r = np.zeros(7); r[D[c]] = 1; r[D[a]] = -1; return r
def mn(a, v):
    r = np.zeros(7); r[D[a]] = -1; return r, -v
Arows = [ge("Education", "Affordability"), ge("Mobility", "Affordability")]; brows = [0.0, 0.0]
for a in ("Mobility", "Education", "Safety"):
    r, v = mn(a, 1 / 7); Arows.append(r); brows.append(v)
A7 = np.vstack(rowsA + [np.array(Arows)]); b7 = np.concatenate(rowsb + [np.array(brows)])
Wp = domain_weights(MP, thP)
ref = hit_and_run(A7, b7, Wp.mean(0), 10000, 200, 5000, hr)
OUT["D1_domain_weights_vs_hit_and_run"] = ks_table(Wp, ref, DOMAINS)

# D1b. domain weights against an exact uniform reference: plain rejection from the flat Dirichlet on the 7 weights
def w_ok(Wx):
    return ((Wx.min(1) >= DOM_LO) & (Wx.max(1) <= DOM_HI) & (Wx[:, D["Education"]] >= Wx[:, D["Affordability"]]) &
            (Wx[:, D["Mobility"]] >= Wx[:, D["Affordability"]]) & (Wx[:, D["Mobility"]] >= 1 / 7) &
            (Wx[:, D["Education"]] >= 1 / 7) & (Wx[:, D["Safety"]] >= 1 / 7))
er = np.random.default_rng(99); exact = []
while sum(len(e) for e in exact) < 60000:
    Wx = er.dirichlet(np.ones(7), 5_000_000); exact.append(Wx[w_ok(Wx)])
exact = np.vstack(exact)
d1b = {"reference_size": len(exact)}
for sd in (42, 1001, 1002):                     # 42 = the Table 1 draw
    Ws = Wp if sd == 42 else domain_weights(MP, MP.sample_theta(10000, np.random.default_rng(sd)))
    d1b[f"seed_{sd}_ks_p"] = {dd: round(float(stats.ks_2samp(Ws[:, i], exact[:, i]).pvalue), 3) for i, dd in enumerate(DOMAINS)}
OUT["D1b_domain_weights_vs_exact_rejection"] = d1b

# D2. measure shares inside a four-measure domain (Mobility), P5 band
idx = [j for j in range(MP.m) if MP.dom[j] == "Mobility"]; nd = len(idx)
sh = thP.reshape(len(thP), MP.m, 3).sum(2)[:, idx]; sh = sh / sh.sum(1, keepdims=True)
I4 = np.eye(nd)
refs = hit_and_run(np.vstack([-I4, -I4, I4]), np.concatenate([np.zeros(nd), -0.6 / nd * np.ones(nd), 1.4 / nd * np.ones(nd)]),
                   np.ones(nd) / nd, 10000, 100, 2000, hr)
OUT["D2_mobility_measure_shares_vs_hit_and_run"] = ks_table(sh, refs, [MP.inds[j] for j in idx])

# D3. segment shares of one measure: g0 >= g1 >= g2 >= 0.1
g = thP.reshape(len(thP), MP.m, 3)[:, 0]; g = g / g.sum(1, keepdims=True)
Ag = np.array([[-1, 1, 0], [0, -1, 1], [0, 0, -1], [-1, 0, 0], [0, -1, 0]], float); bg = np.array([0, 0, -LAST_SEG_MIN, 0, 0])
refg = hit_and_run(Ag, bg, np.array([0.5, 0.3, 0.2]), 10000, 100, 2000, hr)
OUT["D3_segment_shares_vs_hit_and_run"] = ks_table(g, refg, ["g0", "g1", "g2"])
ps = [v["ks_p"] for key in ("D1_domain_weights_vs_hit_and_run", "D2_mobility_measure_shares_vs_hit_and_run",
                            "D3_segment_shares_vs_hit_and_run") for v in OUT[key].values()]
ps += [p for key, v in d1b.items() if key.startswith("seed") for p in v.values()]
OUT["D_summary"] = {"tests": len(ps), "min_p": min(ps), "bonferroni_threshold_5pct": round(0.05 / len(ps), 4),
                    "all_pass_bonferroni": bool(min(ps) > 0.05 / len(ps))}

# ---------------------------------------------------------------- E. independence between levels
OUT["E_level_independence_max_abs_corr"] = round(float(max(
    abs(np.corrcoef(Wp[:, D["Mobility"]], sh[:, i])[0, 1]) for i in range(nd))), 4)

# ---------------------------------------------------------------- F. domain-weight marginals: Theta vs Theta_S
MB = Model(SPEC_M2)
Wb = domain_weights(MB, MB.sample_theta(10000, np.random.default_rng(3)))
OUT["F_domain_weight_marginals"] = {d: {"Theta_mean": round(float(Wb[:, i].mean()), 4), "ThetaS_mean": round(float(Wp[:, i].mean()), 4),
                                        "ThetaS_p05_p95": [round(float(np.percentile(Wp[:, i], 5)), 4), round(float(np.percentile(Wp[:, i], 95)), 4)]}
                                    for i, d in enumerate(DOMAINS)}

# ---------------------------------------------------------------- G. Monte Carlo spread over seeds
seeds = []
for sd in (1, 2, 3, 4, 5):
    g_ = np.random.default_rng(1000 + sd)
    r = smaa(MP.sample_theta(10000, g_), g_)
    seeds.append(float((r[:, SEA] == 1).mean()))
OUT["G_seattle_p_first_other_seeds"] = {"values": [round(v, 4) for v in seeds], "mean": round(float(np.mean(seeds)), 4),
                                        "sd": round(float(np.std(seeds, ddof=1)), 4)}

# ---------------------------------------------------------------- H. uniform over the whole Theta_S (design sensitivity)
A60 = np.vstack([MP.A_ub, -np.eye(MP.n)]); b60 = np.concatenate([MP.b_ub, np.zeros(MP.n)])
chains = []
for c in range(4):
    x0 = thP[c * 2500:(c + 1) * 2500].mean(0)                    # interior starting point
    chains.append(hit_and_run(A60, b60, x0, 2500, 400, 100000, np.random.default_rng(100 + c)))
thU = np.vstack(chains)
OUT["H_hit_and_run_feasible"] = bool(all(MP.feasible(t) for t in thU))
Wu = domain_weights(MP, thU)
cm = np.array([domain_weights(MP, ch).mean(0) for ch in chains])
OUT["H_chain_means_max_spread"] = round(float((cm.max(0) - cm.min(0)).max()), 4)
OUT["H_domain_weight_means_uniform_over_ThetaS"] = {d: round(float(Wu[:, i].mean()), 4) for i, d in enumerate(DOMAINS)}
OUT["H_measures_per_domain"] = {d: MP.dom.count(d) for d in DOMAINS}
rU = smaa(thU, np.random.default_rng(77))
OUT["H_smaa_uniform_over_ThetaS"] = summary(rU)
OUT["H_smaa_level_by_level_table1"] = summary(rP)

(RES / "smaa_sampling_audit.json").write_text(json.dumps(OUT, indent=1, ensure_ascii=False))
print(json.dumps(OUT, indent=1, ensure_ascii=False))
