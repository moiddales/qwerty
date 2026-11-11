"""Figures for the paper from results/*.csv. Run after run_model.py, run_extensions.py and run_preferences.py.

    cd projects/himcm2026A/analysis/model && python make_figures.py
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from core import RES, DOMAINS

FIG = RES / "figures"
FIG.mkdir(exist_ok=True)
SURF, INK, INK2, GRID, GRAY = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df", "#b5b4ad"
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]   # validated categorical order
CITYC = {"Denver": CAT[0], "Seattle": CAT[1], "Chicago": CAT[2], "Austin": CAT[3], "Columbus": CAT[4], "New York": CAT[6]}
SEQ = ["#fcfcfb", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "font.size": 9,
                     "axes.edgecolor": GRAY, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "text.color": INK, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
                     "axes.titlesize": 11, "axes.titlelocation": "left"})


def save(fig, name):
    fig.savefig(FIG / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# 1. reference ranking with domain contributions and floor status
ref = pd.read_csv(RES / "M2_reference_ranking.csv", dtype={"city_id": str}).sort_values("rank_ref", ascending=False)
fl = pd.read_csv(RES / "floors_status.csv", dtype={"city_id": str}).set_index("city").status
fig, ax = plt.subplots(figsize=(7.5, 7.2))
left = np.zeros(len(ref))
for k, d in enumerate(DOMAINS):
    ax.barh(ref.city, ref[d], left=left, color=CAT[k], height=0.72, edgecolor=SURF, linewidth=1.5, label=d)
    left += ref[d].values
for y, (c, u) in enumerate(zip(ref.city, ref.U_ref)):
    tag = {"fail": "  floor: fail", "pending": "  floor: pending"}.get(fl[c], "")
    ax.text(u + 0.005, y, f"{u:.3f}{tag}", va="center", fontsize=8, color=INK2)
ax.set_xlim(0, 1.0); ax.set_xlabel("Reference value U (0 = worst reference node everywhere, 1 = best)")
ax.xaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.45, 1.0), frameon=False, fontsize=8)
ax.set_title("Reference ranking (model M2) by domain contribution", pad=34)
save(fig, "fig1_reference_ranking")

# 2. SMAA rank acceptability
acc = pd.read_csv(RES / "M2_smaa_rank_acceptability.csv", index_col=0)
order = pd.read_csv(RES / "M2_smaa_broad.csv").city
acc = acc.loc[order]
fig, ax = plt.subplots(figsize=(8, 6.6))
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("seq", SEQ)
im = ax.imshow(acc.values, cmap=cmap, vmin=0, vmax=0.5, aspect="auto")
ax.set_yticks(range(len(acc))); ax.set_yticklabels(acc.index)
ax.set_xticks(range(0, 25, 2)); ax.set_xticklabels(range(1, 26, 2)); ax.set_xlabel("Rank")
for i in range(len(acc)):
    for j in range(3):
        v = acc.values[i, j]
        if v >= 0.05:
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7, color=SURF if v > 0.25 else INK)
cb = fig.colorbar(im, ax=ax, fraction=0.03); cb.set_label("Share of simulations"); cb.outline.set_visible(False)
ax.spines[:].set_visible(False)
ax.set_title("SMAA rank acceptability (broad preferences + data noise, 10,000 runs)")
save(fig, "fig2_smaa_rank_acceptability")

# 3. champion as one domain's share changes
sw = pd.read_csv(RES / "M2_champion_by_domain_share.csv", index_col=0)
fig, ax = plt.subplots(figsize=(7.5, 3.6))
for y, d in enumerate(DOMAINS):
    s = sw[sw.domain == d].reset_index(drop=True)
    ends = list(s.from_share[1:]) + [0.6]
    for (_, r), e in zip(s.iterrows(), ends):
        ax.barh(y, e - r.from_share, left=r.from_share, color=CITYC.get(r.champion, GRAY), height=0.62, edgecolor=SURF, linewidth=2)
        if e - r.from_share > 0.06:
            ax.text((r.from_share + e) / 2, y, r.champion, ha="center", va="center", fontsize=7.5, color=SURF)
ax.axvline(1 / 7, color=INK, linewidth=1, linestyle=(0, (3, 2)))
ax.text(1 / 7 + 0.005, len(DOMAINS) - 0.45, "reference 1/7", fontsize=7.5, color=INK2)
ax.set_yticks(range(len(DOMAINS))); ax.set_yticklabels(DOMAINS); ax.invert_yaxis()
ax.set_xlim(0, 0.6); ax.set_xlabel("Weight of the domain (other domains rescaled proportionally)")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=CITYC[c], label=c) for c in ("Denver", "Seattle", "Chicago", "Austin")], ncol=4, frameon=False,
          loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=8)
ax.set_title("Champion as one domain's weight changes", pad=22)
save(fig, "fig3_champion_by_domain_weight")

# 4. preference information curve
pc = pd.read_csv(RES / "preference_information_curve.csv")
fig, ax = plt.subplots(figsize=(6.5, 3.4))
for k, (setname, lab) in enumerate((("indicator-level", "Indicator split free inside domains\n(floor 1/3 → 0.85 of equal share)"), ("domain-level (theta0 shapes)", "Inside-domain split fixed at reference"))):
    s = pc[pc.set == setname]
    ax.plot(range(len(s)), s.necessary_pairs_of_300, color=CAT[k], linewidth=2, marker="o", markersize=6)
    ax.text(len(s) - 1 + 0.1, s.necessary_pairs_of_300.iloc[-1], lab, color=INK2, fontsize=8, va="center")
ax.set_xticks(range(4)); ax.set_xticklabels(["1/14 to 2/7", "±50%", "±25%", "±10%"])
ax.set_xlabel("Allowed range of each domain weight around 1/7"); ax.set_ylabel("City pairs with a fixed order (of 300)")
ax.set_xlim(-0.2, 5.2); ax.yaxis.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
ax.set_title("How much preference information fixes the ranking")
save(fig, "fig4_preference_information")

# 5. revisions M0 -> M1 -> M2
rv = pd.read_csv(RES / "revision_M0_M1_M2.csv")
fig, ax = plt.subplots(figsize=(6, 6.6))
hl = rv[(rv.rank_M0 - rv.rank_M2).abs() >= 3].city.tolist() + ["Denver", "Seattle", "Chicago"]
for _, r in rv.iterrows():
    on = r.city in hl
    c = CITYC[r.city] if r.city in ("Denver", "Seattle", "Chicago") else (INK2 if on else GRAY)
    ax.plot([0, 1, 2], [r.rank_M0, r.rank_M1, r.rank_M2], color=c, linewidth=2 if on else 1, marker="o", markersize=4, zorder=3 if on else 1)
    ax.text(2.06, r.rank_M2, r.city, va="center", fontsize=7.5, color=INK if on else INK2)
    ax.text(-0.06, r.rank_M0, r.city, va="center", ha="right", fontsize=7.5, color=INK if on else INK2)
ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["M0 initial", "M1 data fixes", "M2 accessibility"])
ax.set_ylim(25.7, 0.3); ax.set_yticks([1, 5, 10, 15, 20, 25]); ax.set_ylabel("Reference rank"); ax.set_xlim(-0.75, 2.75)
ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False); ax.tick_params(length=0)
ax.set_title("Rank changes through the two data-driven revisions")
save(fig, "fig5_revisions")

# 6. student profiles
pr = pd.read_csv(RES / "student_profiles.csv")
rows = []
for _, r in pr.iterrows():
    d = {c.rsplit(" ", 1)[0]: float(c.rsplit(" ", 1)[1]) for c in r.smaa_p_first.split("; ")}
    rows.append(d)
pf = pd.DataFrame(rows, index=pr.profile).fillna(0)
cols = [c for c in ["Denver", "Seattle", "Chicago", "Columbus", "New York"] if c in pf]
pf["Other"] = (1 - pf[cols].sum(axis=1)).clip(lower=0)
fig, ax = plt.subplots(figsize=(7.5, 3.8))
left = np.zeros(len(pf))
for c in cols + ["Other"]:
    ax.barh(pf.index, pf[c], left=left, color=CITYC.get(c, GRAY), height=0.66, edgecolor=SURF, linewidth=1.5, label=c)
    for y, (l, v) in enumerate(zip(left, pf[c])):
        if v >= 0.08:
            ax.text(l + v / 2, y, f"{v:.2f}", ha="center", va="center", fontsize=7.5, color=SURF)
    left += pf[c].values
ax.invert_yaxis(); ax.set_xlim(0, 1); ax.set_xlabel("Share of simulations ranked first among eligible cities")
ax.legend(ncol=6, loc="lower center", bbox_to_anchor=(0.35, 1.0), frameon=False, fontsize=8)
ax.set_title("Who wins for different students and families", pad=24)
save(fig, "fig6_student_profiles")

# 7. affordability floor by household income
sc = pd.read_csv(RES / "floors_scan.csv")
inc = sc[sc.scan == "income"]
fig, ax = plt.subplots(figsize=(6.2, 3.2))
ax.bar(range(len(inc)), 25 - inc.n_fail, color=CAT[0], width=0.6, edgecolor=SURF)
for x, (_, r) in enumerate(inc.iterrows()):
    ax.text(x, 25 - r.n_fail + 0.4, f"{25 - r.n_fail} cities\nbest: {r.champion_eligible}", ha="center", fontsize=7.5, color=INK2)
ax.set_xticks(range(len(inc))); ax.set_xticklabels([f"${v // 1000}k" for v in inc.value])
ax.set_ylim(0, 31); ax.set_ylabel("Cities passing all floors"); ax.set_xlabel("Household income (rent floor: 2-bedroom rent ≤ 50% of income)")
ax.set_title("Eligible cities and the eligible leader by household income")
save(fig, "fig7_income_floor_scan")

# 8. transit accessibility: city mean vs lowest-access 20% of residents
eq = pd.read_csv(RES / "equity_within_city.csv")
fig, ax = plt.subplots(figsize=(6.2, 4.6))
ax.scatter(eq.access_mean_kjobs, eq.access_lower20_mean_kjobs.clip(lower=0.5), s=40, color=CAT[0], edgecolor=SURF, linewidth=1.5, zorder=3)
OFF = {"Boston": (-34, 3), "Washington": (-58, -11), "Seattle": (5, -9), "Philadelphia": (-62, 0), "Chicago": (5, 3),
       "Dallas": (-30, 3), "Houston": (5, -2), "Phoenix": (-38, 3), "Columbus": (5, -7), "San Francisco": (5, 4)}
zero = eq[eq.access_lower20_mean_kjobs < 0.5]
for _, r in eq[eq.access_lower20_mean_kjobs >= 0.5].iterrows():
    ax.annotate(r.city, (r.access_mean_kjobs, r.access_lower20_mean_kjobs), xytext=OFF.get(r.city, (4, 2)), textcoords="offset points", fontsize=7, color=INK2)
ax.text(0.02, 0.06, "Lowest 20% reach under 500 jobs (shown at 0.5):\n" + ", ".join(zero.sort_values("access_mean_kjobs").city),
        transform=ax.transAxes, fontsize=7, color=INK2, va="bottom", wrap=True)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Mean jobs reachable in 45 min by transit (thousands, log)")
ax.set_ylabel("Mean for lowest-access 20% (thousands, log; 0 shown at 0.5)")
ax.grid(True, color=GRID, linewidth=0.6); ax.set_axisbelow(True)
ax.set_title("Transit accessibility: city average vs residents with least access")
save(fig, "fig8_access_distribution")
print(sorted(p.name for p in FIG.iterdir()))
