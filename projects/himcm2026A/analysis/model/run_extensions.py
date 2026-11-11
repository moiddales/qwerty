"""Extensions on the final model M2: preference-information analysis, student profiles, cross-checks, numerical verification.

    cd projects/himcm2026A/analysis/model && python run_model.py && python run_extensions.py
"""
import json
import itertools
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import linprog
import core
from core import Model, SPEC_M2, DOMAINS, FLOORS, RES, load, fill_missing, ranks

rng = np.random.default_rng(7)
names, X, S = load()
CITY, CID, nC = names.values, names.index, len(names)
M = Model(SPEC_M2)
Xr = fill_missing(X[M.inds])
PH = M.phi(Xr.values)
U = PH @ M.theta0
OUT = {}
IDX = {c: i for i, c in enumerate(CITY)}
contrib = (PH * M.theta0).reshape(nC, M.m, 3).sum(2)
DS = np.stack([contrib[:, [j for j in range(M.m) if M.dom[j] == d]].sum(1) * 7 for d in DOMAINS], 1)   # domain score 0-1 with theta0 inside domains


def tab(df, name):
    df.to_csv(RES / f"{name}.csv")


# ---------------------------------------------------------------- 1. how much preference information settles the ranking
def pair_stats(lp_min):
    """lp_min(c) returns min of c'w over the set. Returns necessary-pair count, possible winners, regret."""
    dmax = np.zeros((nC, nC))                     # dmax[a, b] = max over the set of U_a - U_b
    for a in range(nC):
        for b in range(nC):
            if a != b:
                dmax[a, b] = -lp_min(-(G[a] - G[b]))
    nec = sum(1 for a in range(nC) for b in range(nC) if a != b and dmax[b, a] <= 0)   # a beats b for every preference
    return nec, dmax


band_rows = []
# (a) full indicator-level set, shrinking the domain band and raising the within-domain floor
for band, frac in ((None, None), (0.5, 1 / 3), (0.25, 0.6), (0.1, 0.85)):
    if band is not None:
        core.DOM_LO, core.DOM_HI, core.IND_MIN_FRAC = (1 - band) / 7, (1 + band) / 7, frac
    m = Model(SPEC_M2)
    G = PH
    nec, dmax = pair_stats(lambda c: m.lp(c).fun)
    regret = dmax.max(0)
    band_rows.append({"set": "indicator-level", "domain_band": "1/14-2/7" if band is None else f"1/7 +/- {int(band * 100)}%",
                      "indicator_min_share_of_equal": round(core.IND_MIN_FRAC, 2), "necessary_pairs_of_300": nec,
                      "cities_never_beaten_necessarily": int(sum(all(dmax[i, k] > 0 for k in range(nC) if k != i) for i in range(nC))),
                      "min_regret_city": CITY[regret.argmin()], "min_regret": round(regret.min(), 4)})
core.DOM_LO, core.DOM_HI, core.IND_MIN_FRAC = 1 / 14, 2 / 7, 1 / 3


# (b) only the seven domain weights uncertain; shapes inside domains fixed at theta0
def dom_lp_factory(lo, hi, extra=()):
    A = [np.eye(7), -np.eye(7)] + [np.atleast_2d(r) for r in extra]
    b = [np.full(7, hi), np.full(7, -lo)] + [np.zeros(1) for _ in extra]
    A, b = np.vstack(A), np.concatenate(b)
    return lambda c: linprog(c, A_ub=A, b_ub=b, A_eq=np.ones((1, 7)), b_eq=[1], bounds=[(0, None)] * 7, method="highs").fun


G = DS / 7
for band in (1.0, 0.5, 0.25, 0.1):
    lo, hi = ((1 / 14, 2 / 7) if band == 1.0 else ((1 - band) / 7, (1 + band) / 7))
    nec, dmax = pair_stats(dom_lp_factory(lo, hi))
    regret = dmax.max(0)
    band_rows.append({"set": "domain-level (theta0 shapes)", "domain_band": "1/14-2/7" if band == 1.0 else f"1/7 +/- {int(band * 100)}%",
                      "indicator_min_share_of_equal": None, "necessary_pairs_of_300": nec,
                      "cities_never_beaten_necessarily": int(sum(all(dmax[i, k] > 0 for k in range(nC) if k != i) for i in range(nC))),
                      "min_regret_city": CITY[regret.argmin()], "min_regret": round(regret.min(), 4)})
tab(pd.DataFrame(band_rows).set_index("set"), "preference_information_curve")
OUT["preference_information_curve"] = band_rows

# which single domain-order statement w_a >= w_b decides the top pairs
top3 = [CITY[i] for i in np.argsort(-U)[:3]]
delta = pd.DataFrame({f"{a} - {b}": DS[IDX[a]] - DS[IDX[b]] for a, b in itertools.combinations(top3, 2)}, index=DOMAINS)
tab(delta.round(4), "top3_domain_score_differences")
voi = []
for a, b in itertools.combinations(top3, 2):
    c = (DS[IDX[a]] - DS[IDX[b]]) / 7
    for d1, d2 in itertools.permutations(range(7), 2):
        r = np.zeros(7); r[d2] = 1; r[d1] = -1           # w_d1 >= w_d2
        f = dom_lp_factory(1 / 14, 2 / 7, [r])
        lo, hi = f(c), -f(-c)
        if lo >= 0 or hi <= 0:
            voi.append({"pair": f"{a} vs {b}", "statement": f"{DOMAINS[d1]} >= {DOMAINS[d2]}",
                        "decides": a if lo >= 0 else b, "min_diff": round(lo, 4), "max_diff": round(hi, 4)})
voi = pd.DataFrame(voi)
tab(voi, "single_statement_decisions")
OUT["single_statements_deciding_top_pairs"] = voi.groupby(["pair", "decides"]).statement.apply(list).to_dict() if len(voi) else {}
OUT["top3_domain_score_differences"] = delta.round(3).to_dict()

# ---------------------------------------------------------------- 2. student and family profiles
bg = pd.read_csv(RES / "sld_block_groups.csv", dtype={"city_id": str})
no_access = bg.assign(z=bg.D5BR0 <= 0).groupby("city_id").apply(lambda g: np.average(g.z, weights=g.TotPop)).reindex(CID)
PROFILES = {
    "reference family ($80k, equal domains)": dict(income=80000, focus=None, extra={}),
    "low-budget family ($50k)": dict(income=50000, focus="Affordability", extra={}),
    "student without a car (transit-dependent)": dict(income=80000, focus="Mobility", extra={"no_transit_access_share_max": 0.25}),
    "activities and sports focus": dict(income=80000, focus="Activities", extra={}),
    "LGBTQ+ student": dict(income=80000, focus="Inclusion", extra={"I1_equality_policy_min": 75}),
    "student needing mental-health support": dict(income=80000, focus="Health", extra={"H3_youth_mh_facilities_min": 5}),
    "academic focus": dict(income=80000, focus="Education", extra={}),
}
prow = []
for name, pf in PROFILES.items():
    _, Xi, _ = load(pf["income"])
    ok = np.ones(nC, bool)
    for k, f in FLOORS.items():
        ok &= Xi[k].values <= f
    if "no_transit_access_share_max" in pf["extra"]:
        ok &= no_access.values <= pf["extra"]["no_transit_access_share_max"]
    if "I1_equality_policy_min" in pf["extra"]:
        ok &= ~(Xi.I1_equality_policy.values < pf["extra"]["I1_equality_policy_min"])      # missing (DC) is not excluded
    if "H3_youth_mh_facilities_min" in pf["extra"]:
        ok &= Xi.H3_youth_mh_facilities.values >= pf["extra"]["H3_youth_mh_facilities_min"]
    ph = M.phi(fill_missing(Xi[M.inds]).values)
    if pf["focus"] is None:
        th0 = M.theta0; ths = M.sample_theta(5000, rng, centre={d: 1 / 7 for d in DOMAINS}, conc=200)
    else:
        prof = {d: (2 / 7 if d == pf["focus"] else (5 / 7) / 6) for d in DOMAINS}
        in_d = np.repeat([d == pf["focus"] for d in M.dom], 3)
        th0 = np.where(in_d, M.theta0 * 2, M.theta0 * (5 / 6))
        ths = M.sample_theta(5000, rng, centre=prof, conc=200)
    u = ph @ th0
    order = [i for i in np.argsort(-u) if ok[i]]
    noisy = Xi[M.inds].values[None] + rng.standard_normal((5000, nC, M.m)) * S[M.inds].values[None]
    noisy = np.where(np.isnan(noisy), fill_missing(Xi[M.inds]).values[None], noisy)
    us = np.vstack([np.einsum("nck,nk->nc", M.phi(noisy[a:a + 500].reshape(-1, M.m)).reshape(-1, nC, M.n), ths[a:a + 500]) for a in range(0, 5000, 500)])
    us[:, ~ok] = -np.inf
    pfirst = np.bincount(us.argmax(1), minlength=nC) / 5000
    best = np.argsort(-pfirst)[:3]
    prow.append({"profile": name, "eligible_cities": int(ok.sum()), "excluded": ";".join(CITY[~ok]),
                 "reference_champion": CITY[order[0]], "reference_top5": ";".join(CITY[order[:5]]),
                 "smaa_p_first": "; ".join(f"{CITY[i]} {pfirst[i]:.2f}" for i in best)})
prof_df = pd.DataFrame(prow).set_index("profile")
tab(prof_df, "student_profiles")
OUT["profiles"] = prof_df[["reference_champion", "smaa_p_first", "eligible_cities"]].to_dict("index")

# ---------------------------------------------------------------- 3. cross-checks with independent sources
sc = pd.read_csv(RES.parent / "supplement_20261111/transit/schedule_coverage.csv", dtype={"city_id": str})
g = sc.groupby("city_id")[["service_rows_20261118", "service_rows_20261114", "service_rows_20261115"]].sum()
g = g[g.service_rows_20261118 > 0]
gtfs_wk = ((g.service_rows_20261114 + g.service_rows_20261115) / 2 / g.service_rows_20261118).reindex(CID)
ok = gtfs_wk.notna()
OUT["gtfs_2026_weekend_ratio_vs_ntd"] = {"n": int(ok.sum()), "spearman": round(stats.spearmanr(gtfs_wk[ok], X.M4r_weekend_retention[ok])[0], 3),
                                         "excluded_no_reference_week_service": CITY[~ok.values].tolist()}
obs = pd.read_csv(RES.parent / "data/processed/observations_all_levels.csv.gz", dtype=str, low_memory=False,
                  usecols=["source_id", "indicator_id", "value", "raw_value", "observation_period", "geography_type", "city_id", "source_geo_id"])
sch = obs[(obs.source_id == "S05") & (obs.observation_period == "2023-24") & obs.geography_type.str.startswith("school point")]
sw = sch.pivot_table(index=["city_id", "source_geo_id"], columns="indicator_id", values="raw_value", aggfunc="first")
enr = sw[["TOT_ENR_M", "TOT_ENR_F"]].apply(pd.to_numeric, errors="coerce").clip(lower=0).sum(axis=1)
has = (sw[["SCH_APENR_IND", "SCH_IBENR_IND", "SCH_DUAL_IND"]] == "Yes").any(axis=1)
share = ((enr * has).groupby(level=0).sum() / enr.groupby(level=0).sum()).reindex(CID)
eq = pd.read_csv(RES / "equity_within_city.csv", dtype={"city_id": str}, index_col=0)
eq["student_share_in_schools_offering_AP_IB_or_dual"] = share.round(3)
tab(eq, "equity_within_city")
OUT["advanced_course_access"] = {"lowest": share.sort_values().head(4).rename(index=dict(zip(CID, CITY))).round(3).to_dict(),
                                 "spearman_with_E1_enrolment_rate": round(stats.spearmanr(share, X.E1_adv_course, nan_policy="omit")[0], 3)}

# Chicago: FBI NIBRS counts 2022-25 (11-16k/yr) vs CPD 2021 local report (25,979) suggest a definition gap
pop21 = pd.read_csv(RES.parent / "data/extracted/foundation/population_25cities_2020_2025.csv", dtype=str).set_index("city_id").POPESTIMATE2021.astype(float)
Xc = X[M.inds].copy()
Xc.loc["1714000", "S1_violent_crime"] = 25979 / pop21["1714000"] * 1e5
uc = M.phi(fill_missing(Xc).values) @ M.theta0
OUT["chicago_crime_definition_sensitivity"] = {"rate_fbi_2022_25": round(float(X.loc["1714000", "S1_violent_crime"]), 1),
                                               "rate_cpd_2021_definition": round(float(Xc.loc["1714000", "S1_violent_crime"]), 1),
                                               "chicago_rank_reference": int(ranks(U)[IDX["Chicago"]]), "chicago_rank_cpd_definition": int(ranks(uc)[IDX["Chicago"]]),
                                               "champion_cpd_definition": CITY[int(np.argmax(uc))]}

# ---------------------------------------------------------------- 4. numerical verification
ver = {}
ths = M.sample_theta(3000, rng)
ver["sampled_theta_inside_set"] = float(np.mean([M.feasible(t) for t in ths]))
dmin = pd.read_csv(RES / "M2_pairwise_min_difference.csv", index_col=0).values
dmax = pd.read_csv(RES / "M2_pairwise_max_difference.csv", index_col=0).values
diff = (PH @ ths.T)                                            # cities x samples
sd = diff[:, None, :] - diff[None, :, :]
ver["sampled_differences_within_LP_bounds"] = bool(np.all(sd.min(2) >= dmin - 1e-3) and np.all(sd.max(2) <= dmax + 1e-3))
ver["max_LP_slack_vs_samples"] = round(float(np.max(dmax - sd.max(2))), 4)
reg_lp = dmax.max(0)
reg_s = (diff.max(0)[None, :] - diff).max(1)
ver["LP_regret_ge_sampled_regret"] = bool(np.all(reg_lp >= reg_s - 1e-6))
i = int(np.argmax(U)); manual = 0.0
for j, ind in enumerate(M.inds):
    x = Xr.iloc[i, j]; t = M.nodes[j]
    for l in range(3):
        manual += M.theta0[3 * j + l] * min(max((x - t[l]) / (t[l + 1] - t[l]), 0), 1)
ver["champion_score_by_hand_equals_matrix"] = bool(abs(manual - U[i]) < 1e-12)
ver["theta0_inside_set"] = M.feasible(M.theta0)
ver["smaa_max_monte_carlo_se_10000"] = round(float(np.sqrt(0.25 / 10000)), 4)
ref = pd.read_csv(RES / "M2_reference_ranking.csv", dtype={"city_id": str}, index_col=0)
ver["domain_contributions_sum_to_U"] = bool(np.allclose(ref[DOMAINS].sum(axis=1), ref.U_ref, atol=1e-3))
OUT["verification"] = ver
json.dump(OUT, open(RES / "extensions_summary.json", "w"), indent=1, ensure_ascii=False, default=float)
print(json.dumps(OUT, indent=1, ensure_ascii=False, default=float))
