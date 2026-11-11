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

# ---------------------------------------------------------------- 6. diagnostics for the remaining risk-register items
dg = {}
cov = PH.reshape(nC, MP.m, 3)
dg["segments_all_0_or_all_1"] = [f"{MP.inds[j]} seg{l + 1}" for j in range(MP.m) for l in range(3)
                                 if np.all(cov[:, j, l] <= 0) or np.all(cov[:, j, l] >= 1)]
dg["cities_at_or_beyond_node_range_share"] = round(float(np.mean((Xr.values - MP.nodes[:, 0]) * good_dir <= 0) + np.mean((Xr.values - MP.nodes[:, 3]) * good_dir >= 0)), 3)
dg["theta0_in_theta_plan"] = MP.feasible(MP.theta0)
contrib = (PH * MP.theta0).reshape(nC, MP.m, 3).sum(2)
dom_score = np.stack([contrib[:, [j for j in range(MP.m) if MP.dom[j] == d]].sum(1) * 7 for d in DOMAINS], 1)
dg["min_domain_score"] = [CITY[int(dom_score.min(1).argmin())], DOMAINS[int(dom_score.min(0).argmin())], round(float(dom_score.min()), 3)]
r = pd.DataFrame(Xr.values * good_dir, columns=MP.inds).corr(method="spearman")
pairs = [(a, b, round(r.loc[a, b], 3)) for i, a in enumerate(MP.inds) for b in MP.inds[i + 1:] if abs(r.loc[a, b]) >= 0.6]
dg["indicator_pairs_abs_spearman_ge_0.6"] = sorted(pairs, key=lambda t: -abs(t[2]))
obs = pd.read_csv(RES.parent / "data/processed/observations_all_levels.csv.gz", dtype=str, low_memory=False,
                  usecols=["source_id", "indicator_id", "value", "observation_period", "city_id"])
pov = obs[(obs.source_id == "S02") & (obs.indicator_id == "poverty_pct") & (obs.observation_period == "2020-2024")].set_index("city_id").value.astype(float).reindex(CID)
dg["spearman_grad_district_vs_poverty"] = round(stats.spearmanr(X.E2r_grad_district, pov)[0], 3)
dg["spearman_adv_course_vs_poverty"] = round(stats.spearmanr(X.E1_adv_course, pov)[0], 3)
ref_sw = pd.read_csv(RES / "M2_champion_by_domain_share.csv")
dg["champions_in_one_parameter_scans"] = sorted(ref_sw.champion.unique().tolist())
dg["possible_winners_by_LP_theta_plan"] = int((pd.read_csv(RES / "M2_plan_preferences_robust.csv").possible_winner_margin >= 0).sum())
el = pd.read_csv(RES / "M2_smaa_eligibility.csv")
dg["max_gap_p_first_given_eligible_minus_joint"] = round(float((el.p_first_given_eligible - el.p_eligible_and_first).max()), 4)
OUT["risk_diagnostics"] = dg
json.dump(OUT, open(RES / "robustness_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(dg, indent=1, ensure_ascii=False, default=float))

# ---------------------------------------------------------------- 7. joint feasibility inside cities: affordable rent AND transit access in the same tract
# ACS 2020-24 tract median gross rent and poverty (2020 tracts) mapped to 2010 tracts with the Opportunity Atlas crosswalk,
# then joined to SLD block groups (2010 geography) aggregated to tracts.
A = RES.parent / "data/extracted/foundation/acs"


def acs_tract(table, cols):
    d = pd.read_csv(A / f"2024_5YR_{table}_county_small_areas.csv.gz", dtype=str)
    d = d[d.GEO_ID.str.startswith("1400000US")].copy(); d["tract_2020"] = d.GEO_ID.str[-11:]
    for c in cols:
        d[c] = pd.to_numeric(d[c]); d.loc[d[c] < 0, c] = np.nan
    return d.set_index("tract_2020")[cols]


t20 = acs_tract("B25064", ["B25064_E001"]).join(acs_tract("B17001", ["B17001_E001", "B17001_E002"]))
cw = pd.read_csv(RES.parent / "data/extracted/foundation/opportunity/us_tract_2010_2020_crosswalk_relevant_counties.csv.gz", dtype=str)
long = pd.concat([cw[["tract_2020", f"tract_2010_{k}", f"wgt_{k}"]].set_axis(["tract_2020", "tract_2010", "w"], axis=1) for k in range(1, 6)]).dropna()
long["w"] = long.w.astype(float)
long = long.join(t20, on="tract_2020")
long["wp"] = long.w * long.B17001_E001
ok = long.dropna(subset=["B25064_E001", "wp"])
t10 = pd.DataFrame({"rent": (ok.B25064_E001 * ok.wp).groupby(ok.tract_2010).sum() / ok.wp.groupby(ok.tract_2010).sum()})
okp = long.dropna(subset=["B17001_E002", "w"])
t10["poverty"] = (okp.B17001_E002 * okp.w).groupby(okp.tract_2010).sum() / (okp.B17001_E001 * okp.w).groupby(okp.tract_2010).sum()
bg["tract_2010"] = bg.bg_geoid2019.astype(str).str.zfill(12).str[:11]
tr = bg.groupby(["city_id", "tract_2010"]).apply(lambda g: pd.Series({"pop": g.TotPop.sum(), "access": np.average(g.D5BR0 / 1000, weights=g.TotPop)}),
                                                 include_groups=False).reset_index().join(t10, on="tract_2010")
rows = []
for c, g in tr.groupby("city_id"):
    k = g.dropna(subset=["rent"])
    w = k["pop"]
    row = {"city_id": c, "pop_share_with_rent_data": g.dropna(subset=["rent"])["pop"].sum() / g["pop"].sum()}
    for inc in (80000, 50000):
        aff = k.rent * 12 <= 0.30 * inc
        row[f"share_affordable_{inc // 1000}k"] = np.average(aff, weights=w)
        row[f"share_affordable_and_access60k_{inc // 1000}k"] = np.average(aff & (k.access >= 60), weights=w)
    hp = g[g.poverty >= 0.25]
    row["access_high_poverty_tracts_over_city"] = (np.average(hp.access, weights=hp["pop"]) / np.average(g.access, weights=g["pop"])) if len(hp) else np.nan
    rows.append(row)
jf = pd.DataFrame(rows).set_index("city_id").reindex(CID)
jf.insert(0, "city", CITY)
jf.round(3).to_csv(RES / "joint_feasibility_tracts.csv")
spec = {k: v for k, v in SPEC_M2.items() if k != "M5r_transit_access"}
spec["M5j_affordable_access_share"] = ("Mobility", [0.02, 0.10, 0.30, 0.60], "share of residents in tracts that are affordable at $80k and reach 60k jobs by transit in 45 min")
Xj = X.copy(); Xj["M5j_affordable_access_share"] = jf["share_affordable_and_access60k_80k"].values
mj = Model(spec, STATEMENTS_PLAN)
uj = mj.phi(fill_missing(Xj[mj.inds]).values) @ mj.theta0
OUT["joint_feasibility"] = {
    "min_rent_data_coverage": [jf.city[jf.pop_share_with_rent_data.idxmin()], round(float(jf.pop_share_with_rent_data.min()), 3)],
    "spearman_city_mean_access_vs_affordable_access_share": round(stats.spearmanr(X.M5r_transit_access, jf.share_affordable_and_access60k_80k)[0], 3),
    "highest_affordable_access_share_80k": jf.sort_values("share_affordable_and_access60k_80k", ascending=False).head(5).set_index("city").share_affordable_and_access60k_80k.round(3).to_dict(),
    "lowest_high_poverty_access_ratio": jf.sort_values("access_high_poverty_tracts_over_city").head(4).set_index("city").access_high_poverty_tracts_over_city.round(2).to_dict(),
    "model_with_joint_measure": {"champion": CITY[uj.argmax()], "top5": CITY[np.argsort(-uj)[:5]].tolist(),
                                 "kendall_tau_vs_M2_plan": round(stats.kendalltau(U0, uj)[0], 3)}}
json.dump(OUT, open(RES / "robustness_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(OUT["joint_feasibility"], indent=1, ensure_ascii=False, default=float))

# ---------------------------------------------------------------- 8. geography: air quality from CBSA monitors instead of city-weighted counties
aq = pd.read_csv(RES.parent / "data/processed/observations_all_levels.csv.gz", dtype=str, low_memory=False,
                 usecols=["source_id", "indicator_id", "value", "observation_period", "city_id", "geography_type"])
aq = aq[(aq.source_id == "S10") & (aq.geography_type == "CBSA")]
aq["v"] = pd.to_numeric(aq.value)
w = aq.pivot_table(index=["city_id", "observation_period"], columns="indicator_id", values="v")
bad = ["cbsa_aqi_unhealthy_for_sensitive_groups_days", "cbsa_aqi_unhealthy_days", "cbsa_aqi_very_unhealthy_days", "cbsa_aqi_hazardous_days"]
cbsa = (w[bad].sum(axis=1) / w.cbsa_aqi_days_with_aqi * 100).groupby(level=0).mean().reindex(CID)
Xg = X.copy(); Xg["H1_bad_air_days"] = cbsa.values
ug = MP.phi(fill_missing(Xg[MP.inds]).values) @ MP.theta0
OUT["geography_air_cbsa"] = {"spearman_county_vs_cbsa_air": round(stats.spearmanr(X.H1_bad_air_days, cbsa)[0], 3),
                             "champion": CITY[ug.argmax()], "kendall_tau_vs_M2": round(stats.kendalltau(U0, ug)[0], 3),
                             "floor_fail_air_30pct": CITY[cbsa.values > 30].tolist()}
json.dump(OUT, open(RES / "robustness_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(OUT["geography_air_cbsa"], ensure_ascii=False))
