"""Model-stage deliverables (PLAN 9-10): indicator and compensation table, 25-city master table, one-city worked example.

    cd projects/himcm2026A/analysis/model && python make_tables.py      (after the other scripts)
"""
import numpy as np
import pandas as pd
from core import Model, SPEC_M2, STATEMENTS_PLAN, DOMAINS, FLOORS, RES, load, fill_missing, ranks

names, X, S = load()
CITY, CID, nC = names.values, names.index, len(names)
M = Model(SPEC_M2)
MP = Model(SPEC_M2, STATEMENTS_PLAN)
Xr = fill_missing(X[M.inds])
PH = M.phi(Xr.values)
U0 = PH @ M.theta0
notes = pd.read_csv(RES / "indicator_notes.csv").set_index("indicator").note
notes["C1_rent_share"] = "HUD FY2024 two-bedroom Fair Market Rent x 12 as percent of the $80,000 reference household income"

# ---------------------------------------------------------------- 1. indicator and compensation table
rows = []
for j, ind in enumerate(M.inds):
    dom, nodes, basis = M.spec[ind]
    role = "compensable value"
    if ind in FLOORS:
        role = f"floor ({'<=' if nodes[0] > nodes[3] else '>='} {FLOORS[ind]:g}, not compensable) + compensable value above it"
    rows.append({"indicator": ind, "domain": dom, "definition_and_source": notes[ind.replace("C1_rent_share", "C1_rent_share")],
                 "better": "lower" if nodes[0] > nodes[3] else "higher", "nodes_worst_to_best": " / ".join(f"{v:g}" for v in nodes),
                 "node_basis": basis, "role": role, "veto_in_ELECTRE": "yes (gap >= 0.8 of value scale)",
                 "reference_share_of_total": round(M.theta0[3 * j:3 * j + 3].sum(), 4),
                 "cities_with_data": int(X[ind].notna().sum()), "min": round(X[ind].min(), 2), "median": round(X[ind].median(), 2), "max": round(X[ind].max(), 2)})
tab1 = pd.DataFrame(rows).set_index("indicator")
tab1.to_csv(RES / "table_indicators_and_compensation.csv")

# ---------------------------------------------------------------- 2. 25-city master table
fl = pd.read_csv(RES / "floors_status.csv", dtype={"city_id": str}, index_col=0)
broad = pd.read_csv(RES / "M2_smaa_broad.csv", dtype={"city_id": str}, index_col=0)
rob = pd.read_csv(RES / "M2_robust_preference.csv", dtype={"city_id": str}, index_col=0)
plan = pd.read_csv(RES / "M2_plan_preferences_robust.csv", dtype={"city_id": str}, index_col=0)
el = pd.read_csv(RES / "M2_electre_sampled_weights.csv", index_col=0)
jf = pd.read_csv(RES / "joint_feasibility_tracts.csv", dtype={"city_id": str}, index_col=0)
master = pd.DataFrame({"city": CITY}, index=CID)
master["floor_status_$80k"] = fl.status
master["U_reference"] = U0.round(4)
master["rank_reference"] = ranks(U0)
master["smaa_broad_p_first"] = broad.p_first
master["smaa_broad_rank_90pct"] = broad.rank_p05.astype(int).astype(str) + "-" + broad.rank_p95.astype(int).astype(str)
master["max_regret_broad"] = rob.max_regret
master["theta_plan_possible_winner"] = plan.possible_winner_margin >= 0
master["theta_plan_smaa_p_first"] = plan.smaa_p_first
master["theta_plan_smaa_p_top3"] = plan.smaa_p_top3
master["theta_plan_max_regret"] = plan.max_regret
master["electre_kernel_freq_plan"] = master.city.map(el.p_in_kernel_plan)
master["affordable_and_accessible_residents_$80k"] = jf["share_affordable_and_access60k_80k"]


def verdict(r):
    if r["floor_status_$80k"] == "fail":
        return "not recommended at $80k (floor)"
    if r.theta_plan_smaa_p_first >= 0.5:
        return "leading recommendation"
    if r.theta_plan_smaa_p_first >= 0.1 or r.electre_kernel_freq_plan >= 0.3:
        return "co-leader under some preferences"
    if r.theta_plan_smaa_p_top3 >= 0.1:
        return "contender for top 3"
    if not r.theta_plan_possible_winner:
        return "cannot rank first under stated preferences"
    return "ranked, not a contender"


master["recommendation_status"] = master.apply(verdict, axis=1)
master = master.sort_values(["theta_plan_smaa_p_first", "U_reference"], ascending=False)
master.round(4).to_csv(RES / "table_master_25_cities.csv")

# ---------------------------------------------------------------- 3. worked example: the leading city through every step
city = master.city.iloc[0]
rival = master.city.iloc[1]
i, k = list(CITY).index(city), list(CITY).index(rival)
steps = []
for j, ind in enumerate(M.inds):
    t = M.nodes[j]; x = Xr.iloc[i, j]
    cov = PH[i, 3 * j:3 * j + 3]; th = M.theta0[3 * j:3 * j + 3]
    steps.append({"indicator": ind, "domain": M.dom[j], "raw_value": round(float(X[ind].iloc[i]), 3) if pd.notna(X[ind].iloc[i]) else None,
                  "measurement_sd": round(float(S[ind].iloc[i]), 3), "nodes": " / ".join(f"{v:g}" for v in t),
                  "segment_coverage": " / ".join(f"{c:.3f}" for c in cov), "theta0_segments": " / ".join(f"{v:.4f}" for v in th),
                  "contribution": round(float(cov @ th), 4), "rival_contribution": round(float(PH[k, 3 * j:3 * j + 3] @ th), 4)})
we = pd.DataFrame(steps).set_index("indicator")
we.to_csv(RES / f"worked_example_{city.replace(' ', '_')}.csv")
c = PH[i] - PH[k]
lo_b, hi_b = M.lp(c).fun, -M.lp(-c).fun
lo_p, hi_p = MP.lp(c).fun, -MP.lp(-c).fun
fl_i = fl.loc[CID[i]]
lines = [f"# Worked example: {city} through the full model (M2)\n",
         "Generated by `analysis/model/make_tables.py` from the results files; every number below is recomputed there.\n",
         "## Step 1. Floors (not compensable)\n", "| Floor | Value | Threshold | 90% state |", "|---|---|---|---|"]
for f, thr in FLOORS.items():
    lines.append(f"| {f} | {fl_i[f]:.2f} | {thr:g} | {fl_i[f + '_state']} |")
lines += [f"\nJoint pass probability (simulation): {fl_i.p_joint_simulation:.3f}; status: **{fl_i.status}**.\n",
          "## Step 2. Piecewise value: segment coverage x reference parameters\n",
          f"Each indicator value is placed between its four fixed nodes; coverage of each segment is clip((x - t_l)/(t_(l+1) - t_l), 0, 1). The contribution is coverage x theta0. Full table: `results/worked_example_{city.replace(' ', '_')}.csv`.\n",
          "| Domain | " + city + " | " + rival + " | Difference |", "|---|---|---|---|"]
for d in DOMAINS:
    a, b = we[we.domain == d].contribution.sum(), we[we.domain == d].rival_contribution.sum()
    lines.append(f"| {d} | {a:.4f} | {b:.4f} | {a - b:+.4f} |")
lines += [f"| **Total U** | **{U0[i]:.4f}** | **{U0[k]:.4f}** | **{U0[i] - U0[k]:+.4f}** |\n",
          "## Step 3. Robust preference against the closest rival (linear programmes)\n",
          f"min and max of U({city}) - U({rival}) over the preference set:\n",
          f"- Broad set Theta: [{lo_b:.4f}, {hi_b:.4f}]",
          f"- Stated preferences Theta_PLAN: [{lo_p:.4f}, {hi_p:.4f}]\n",
          ("Both intervals contain 0, so the order of the two cities depends on preferences in both sets.\n" if lo_b < 0 < hi_b and lo_p < 0 < hi_p
           else "At least one interval excludes 0, so the order is fixed in that set.\n"),
          "## Step 4. Ranking support, regret and outranking\n",
          f"| Measure | {city} | {rival} |", "|---|---|---|"]
for col, lab in (("smaa_broad_p_first", "SMAA first place, broad"), ("theta_plan_smaa_p_first", "SMAA first place, Theta_PLAN"),
                 ("theta_plan_smaa_p_top3", "SMAA top 3, Theta_PLAN"), ("max_regret_broad", "Max regret, broad"),
                 ("theta_plan_max_regret", "Max regret, Theta_PLAN"), ("electre_kernel_freq_plan", "ELECTRE kernel frequency, Theta_PLAN"),
                 ("affordable_and_accessible_residents_$80k", "Residents in affordable + accessible tracts ($80k)")):
    lines.append(f"| {lab} | {master.set_index('city').loc[city, col]:.3f} | {master.set_index('city').loc[rival, col]:.3f} |")
lines.append(f"\nRecommendation status: {city} — {master.set_index('city').loc[city, 'recommendation_status']}; {rival} — {master.set_index('city').loc[rival, 'recommendation_status']}.")
(RES / "WORKED_EXAMPLE.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(master[["city", "floor_status_$80k", "rank_reference", "theta_plan_smaa_p_first", "theta_plan_max_regret", "recommendation_status"]].to_string())
print("\n".join(lines))
