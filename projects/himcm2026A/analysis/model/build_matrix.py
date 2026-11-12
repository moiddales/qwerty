"""Build the 25-city indicator matrix (raw values and measurement SD) from the archived data.

Run from the repository root after restore_city_archive.py --extract:
    python projects/himcm2026A/analysis/model/build_matrix.py
Outputs: projects/himcm2026A/results/indicator_matrix.csv, indicator_sd.csv, indicator_notes.csv
"""
from pathlib import Path
import numpy as np
import pandas as pd

P = Path(__file__).resolve().parents[2]
D = P / "data"
OUT = P / "results"
OUT.mkdir(exist_ok=True)

cities = pd.read_csv(D / "metadata/cities.csv", dtype=str)
CID = cities.city_id.tolist()
obs = pd.read_csv(D / "processed/observations_all_levels.csv.gz", dtype=str, low_memory=False)
obs["v"] = pd.to_numeric(obs.value, errors="coerce")

X = pd.DataFrame(index=CID)   # point values
S = pd.DataFrame(index=CID)   # measurement SD of the point value
notes = []


def note(ind, text):
    notes.append({"indicator": ind, "note": text})


pop = pd.read_csv(D / "extracted/foundation/population_25cities_2020_2025.csv", dtype=str).set_index("city_id")
POP = pop[[f"POPESTIMATE{y}" for y in range(2020, 2026)]].astype(float)
POP.columns = [str(y) for y in range(2020, 2026)]

# ACS 2020-24 five-year age table: under-18 and approximate 14-18 population
b = pd.read_csv(D / "extracted/foundation/acs/2024_5YR_B01001_cities.csv", dtype=str)
b.index = b.GEO_ID.str[-7:]
e = lambda k: b[f"B01001_E{k:03d}"].astype(float)
under18 = sum(e(k) for k in (3, 4, 5, 6, 27, 28, 29, 30))
age14_18 = (e(5) + e(29)) / 5 + e(6) + e(30) + (e(7) + e(31)) / 2   # 1/5 of 10-14, all 15-17, 1/2 of 18-19


def two_wave(v_new, v_old):
    """Point value = newer wave; SD from the difference of two waves."""
    return v_new, (v_new - v_old).abs() / np.sqrt(2)


# ---------- CRDC city sums (high-school-offering schools located in the city) ----------
ed = pd.read_csv(D / "extracted/education_inclusion/education_city_indicators.csv", dtype=str)
ed["v"] = pd.to_numeric(ed.value, errors="coerce")
crdc = ed.pivot_table(index="city_id", columns=["observation_period", "indicator_id"], values="v")


def crdc_rate(period, num, scale):
    c = crdc[period]
    enr = c["TOT_ENR_M_observed_sum"] + c["TOT_ENR_F_observed_sum"]
    return c[num].sum(axis=1, min_count=1) / enr * scale


adv = ["TOT_APENR_M_observed_sum", "TOT_APENR_F_observed_sum", "TOT_IBENR_M_observed_sum",
       "TOT_IBENR_F_observed_sum", "TOT_DUALENR_M_observed_sum", "TOT_DUALENR_F_observed_sum"]
X["E1_adv_course"], S["E1_adv_course"] = two_wave(crdc_rate("2023-24", adv, 100), crdc_rate("2021-22", adv, 100))
X["E3_counselors"], S["E3_counselors"] = two_wave(crdc_rate("2023-24", ["SCH_FTECOUNSELORS_observed_sum"], 1000),
                                                  crdc_rate("2021-22", ["SCH_FTECOUNSELORS_observed_sum"], 1000))
hs = ["SCH_FTESERVICES_NUR_observed_sum", "SCH_FTESERVICES_PSY_observed_sum", "SCH_FTESERVICES_SOC_observed_sum"]
X["H2_school_health_staff"], S["H2_school_health_staff"] = two_wave(crdc_rate("2023-24", hs, 1000),
                                                                    crdc_rate("2021-22", hs, 1000))
note("E1_adv_course", "AP+IB+dual-enrolment course enrolments per 100 students, CRDC 2023-24; a student in two programmes counts twice; SD from 2021-22 vs 2023-24")
note("E3_counselors", "FTE counsellors per 1,000 students, CRDC 2023-24; SD from two waves")
note("H2_school_health_staff", "FTE nurses+psychologists+social workers per 1,000 students, CRDC 2023-24; counsellors are counted only in E3")


def crdc_module(period, module, cols):
    f = pd.read_csv(D / f"extracted/education_inclusion/crdc_{period}/SCH/{module}.csv", dtype=str)
    v = f[cols].apply(pd.to_numeric, errors="coerce")
    v = v.where(v >= 0)          # negative CRDC reserve codes are missing, not zero
    v["city_id"] = f.city_id
    return v.groupby("city_id").sum(min_count=1)


def module_rate(period, module, cols, scale):
    enr = crdc_module(period, "Enrollment", ["TOT_ENR_M", "TOT_ENR_F"]).sum(axis=1)
    return crdc_module(period, module, cols).sum(axis=1) / enr * scale


X["A3_school_sports"], S["A3_school_sports"] = two_wave(
    module_rate("2324", "Interscholastic_Athletics", ["TOT_PART"], 100),
    module_rate("2122", "Interscholastic_Athletics", ["TOT_PART"], 100))
oss = [f"TOT_DISC{w}_{k}OOS{i}_{g}" for w, i in (("WODIS", ""), ("WDIS", "_IDEA")) for k in ("SING", "MULT") for g in "MF"]
X["I2_suspension"], S["I2_suspension"] = two_wave(module_rate("2324", "Suspensions", oss, 100),
                                                  module_rate("2122", "Suspensions", oss, 100))
ath = pd.read_csv(D / "extracted/education_inclusion/crdc_2324/SCH/Interscholastic_Athletics.csv", dtype=str)
enr_s = pd.read_csv(D / "extracted/education_inclusion/crdc_2324/SCH/Enrollment.csv", dtype=str)
enr_s["enr"] = enr_s[["TOT_ENR_M", "TOT_ENR_F"]].apply(pd.to_numeric, errors="coerce").clip(lower=0).sum(axis=1)
m = enr_s[["city_id", "COMBOKEY", "enr"]].merge(ath[["COMBOKEY", "SCH_ATHLETICS_IND"]], on="COMBOKEY")
ath_share = m[m.SCH_ATHLETICS_IND == "Yes"].groupby("city_id").enr.sum() / m.groupby("city_id").enr.sum()
gap = ath_share[ath_share < 0.25].index          # schools with most students report no programme at all: reporting gap
X.loc[gap, "A3_school_sports"] = np.nan
S.loc[gap, "A3_school_sports"] = np.nan
ath_share.round(3).to_csv(OUT / "audit_athletics_reporting_share.csv", header=["enrolment_share_in_schools_reporting_athletics"])
note("A3_school_sports", f"Missing for {list(gap)}: under 25% of students are in schools that report any athletics programme. " + "Interscholastic athletics participations per 100 students, CRDC 2023-24; a student in two sports counts twice")
note("I2_suspension", "Students with one or more out-of-school suspensions per 100 students, CRDC 2023-24 (with and without disabilities)")

# ---------- graduation, 2020-21 cohort ----------
g = obs[(obs.source_id == "S06") & (obs.observation_period == "2020-2021") & obs.geography_type.str.startswith("school point")]
gw = g.pivot_table(index=["city_id", "source_geo_id"], columns="indicator_id", values="v")
gw = gw.dropna(subset=["ACGR_cohort_count", "ACGR_lower_bound", "ACGR_upper_bound"])
gw = gw[gw.ACGR_cohort_count > 0]
w = gw.ACGR_cohort_count
agg = lambda col: (gw[col] * w).groupby(level=0).sum() / w.groupby(level=0).sum()
lo, hi = agg("ACGR_lower_bound"), agg("ACGR_upper_bound")
grad, grad_sd = (lo + hi) / 2, (hi - lo) / (2 * 1.645)
char = pd.read_csv(D / "extracted/education_inclusion/crdc_2122/SCH/School_Characteristics.csv", dtype=str).set_index("COMBOKEY").SCH_STATUS_CHARTER
xw = pd.read_csv(D / "extracted/education_inclusion/crdc_2122_official_crosswalk_used.csv", dtype=str)
nces_to_crdc = xw.dropna(subset=["NCES SCH 2020-21"]).drop_duplicates("NCES SCH 2020-21").set_index("NCES SCH 2020-21").COMBOKEY   # official ID crosswalk (New York IDs differ)
ids = gw.index.get_level_values(1)
gw["charter"] = ids.map(nces_to_crdc).map(char)
gd = gw[gw.charter == "No"]
wd = gd.ACGR_cohort_count
grad_d = ((gd.ACGR_lower_bound + gd.ACGR_upper_bound) / 2 * wd).groupby(level=0).sum() / wd.groupby(level=0).sum()
top = gw.assign(share=w / w.groupby(level=0).transform("sum"), mid=(gw.ACGR_lower_bound + gw.ACGR_upper_bound) / 2)
top[(top.share > 0.1) & (top.mid < 50)][["ACGR_cohort_count", "mid", "share", "charter"]].round(3).to_csv(OUT / "audit_graduation_outlier_schools.csv")
s28 = obs[(obs.source_id == "S28") & obs.observation_period.str.startswith("2020-21")]
grad["1714000"] = s28[(s28.city_id == "1714000") & (s28.indicator_id == "four_year_adjusted_cohort_graduation_rate")].v.iloc[0]
grad["5363000"] = s28[(s28.city_id == "5363000") & s28.indicator_id.isin(["OSPI_4year_GraduationRate", "four_year_adjusted_cohort_graduation_rate"])].v.iloc[0]
if grad["5363000"] <= 1:
    grad["5363000"] *= 100
grad_sd["1714000"] = grad_sd["5363000"] = 0.0
X["E2_grad_rate"], S["E2_grad_rate"] = grad, grad_sd
grad_d["1714000"], grad_d["5363000"] = grad["1714000"], grad["5363000"]
X["E2r_grad_district"], S["E2r_grad_district"] = grad_d, grad_sd
note("E2r_grad_district", "As E2 but only non-charter schools (CRDC 2021-22 charter flag), i.e. schools a resident enrols in by address")
note("E2_grad_rate", "Cohort-weighted four-year ACGR of schools located in the city, EDFacts 2020-21 (range midpoints for masked values, SD from range width); Chicago and Seattle are whole-district official rates")

# ---------- violent crime, 2022-2025 ----------
ch = pd.read_csv(D / "extracted/safety_health/crime_city_year_source_choice.csv", dtype=str)
ch = ch[(ch.indicator_id == "violent_crime") & ch.year.isin(["2022", "2023", "2024", "2025"])]
cnt = ch.pivot_table(index="city_id", columns="year", values="value", aggfunc=lambda s: float(s.iloc[0]))
fbi = pd.read_csv(D / "extracted/safety_health/fbi_city_wide.csv", dtype=str)
apop = fbi.pivot_table(index="city_id", columns="year", values="agency_population", aggfunc=lambda s: float(s.iloc[0]))
den = POP[["2022", "2023", "2024", "2025"]].copy()
METRO_AGENCY = ["3712000", "3240000", "4752006"]     # Charlotte-Mecklenburg, Las Vegas Metropolitan, Metro Nashville
for c in METRO_AGENCY:
    den.loc[c] = apop.loc[c, ["2022", "2023", "2024", "2025"]]
vr = cnt / den * 1e5
X["S1_violent_crime"], S["S1_violent_crime"] = vr.mean(axis=1), vr.std(axis=1, ddof=1) / 2
# Chicago: the FBI series counts about 3,400 aggravated assaults a year, against 15,606 aggravated assaults and batteries in
# the Chicago Police Department's 2021 report; the FBI series omits aggravated battery. Use the department's 2021 total
# (25,979) over the 2021 population, and keep the FBI series' relative error.
chi_cpd = 25979 / POP.loc["1714000", "2021"] * 1e5
S.loc["1714000", "S1_violent_crime"] *= chi_cpd / X.loc["1714000", "S1_violent_crime"]
X.loc["1714000", "S1_violent_crime"] = chi_cpd
note("S1_violent_crime", "Violent crimes per 100,000, mean of 2022-2025 FBI agency counts (Chicago: CPD 2021 total 25,979, which includes aggravated battery); denominator Census city population, except FBI agency population for Charlotte-Mecklenburg, Las Vegas Metropolitan and Metro Nashville; SD = SD of annual rates / sqrt(4)")

# ---------- traffic deaths, 2021-2024 ----------
f9 = obs[(obs.source_id == "S09")]
fat = f9[f9.indicator_id == "fatalities"].pivot_table(index="city_id", columns="observation_period", values="v")
tr = fat / POP[["2021", "2022", "2023", "2024"]] * 1e5
X["S2_traffic_deaths"], S["S2_traffic_deaths"] = tr.mean(axis=1), tr.std(axis=1, ddof=1) / 2
teen = f9[f9.indicator_id == "fatalities_age14_18"].pivot_table(index="city_id", columns="observation_period", values="v").sum(axis=1)
pd.DataFrame({"deaths_14_18_2021_2024": teen, "person_years_14_18": age14_18 * 4}).to_csv(OUT / "teen_traffic_counts.csv")
note("S2_traffic_deaths", "Traffic deaths per 100,000 residents by crash location, FARS 2021-2024 mean; SD = SD of annual rates / sqrt(4)")

# ---------- air quality, 2021-2024 ----------
a = obs[(obs.source_id == "S10") & (obs.geography_type == "county")].copy()
a["share"] = pd.to_numeric(a.city_population_share, errors="coerce")
bad = ["aqi_unhealthy_for_sensitive_groups_days", "aqi_unhealthy_days", "aqi_very_unhealthy_days", "aqi_hazardous_days"]
aw = a.pivot_table(index=["city_id", "source_geo_id", "observation_period"], columns="indicator_id", values="v")
aw["pct"] = aw[bad].sum(axis=1) / aw["aqi_days_with_aqi"] * 100
sh = a.groupby(["city_id", "source_geo_id", "observation_period"]).share.first()
aw["share"] = sh
aw = aw.dropna(subset=["pct"])
air = (aw.pct * aw.share).groupby(level=[0, 2]).sum() / aw.share.groupby(level=[0, 2]).sum()
air = air.unstack()
X["H1_bad_air_days"], S["H1_bad_air_days"] = air.mean(axis=1), air.std(axis=1, ddof=1) / 2
note("H1_bad_air_days", "Percent of monitored days with AQI above 100, county monitors weighted by the city's residents in each county, EPA 2021-2024 mean")

# ---------- youth mental-health facilities ----------
mh = obs[obs.source_id == "S14"].set_index("city_id").v
X["H3_youth_mh_facilities"] = mh / under18 * 1e5
S["H3_youth_mh_facilities"] = np.sqrt(mh) / under18 * 1e5
note("H3_youth_mh_facilities", "SAMHSA-listed mental-health facilities accepting children/adolescents per 100,000 residents under 18 (facility postal city; no capacity measure); Poisson SD")

# ---------- mobility: SLD block groups inside the city ----------
sel = pd.read_csv(D / "extracted/mobility_opportunities/sld_city_bg_spatial_selection.csv", dtype=str)
sld = pd.read_csv(D / "extracted/mobility_opportunities/sld_selected_block_groups_all_source_fields.csv.gz", dtype=str,
                  usecols=["bg_geoid2019", "TotPop", "D4C", "D4A", "NatWalkInd", "D5BR", "D5AR"])
bg = sel[sel.selection == "contained"].merge(sld, on="bg_geoid2019")
for c in ("TotPop", "D4C", "D4A", "NatWalkInd", "D5BR", "D5AR"):
    bg[c] = pd.to_numeric(bg[c], errors="coerce")
bg["D5BR0"] = bg.D5BR.where(bg.D5BR >= 0, 0.0)  # -99999: no transit within walking distance -> no jobs reachable by transit
bg["D4C0"] = bg.D4C.where(bg.D4C >= 0, 0.0)   # -99999: no transit service within the buffer -> 0 trips per hour
bg = bg[bg.TotPop > 0]
bg[["city_id", "bg_geoid2019", "TotPop", "D4C0", "D4A", "NatWalkInd", "D5BR0", "D5AR"]].to_csv(OUT / "sld_block_groups.csv", index=False)
wmean = lambda col: (bg[col] * bg.TotPop).groupby(bg.city_id).sum() / bg.TotPop.groupby(bg.city_id).sum()
X["M1_transit_frequency"], X["M2_walkability"] = wmean("D4C0"), wmean("NatWalkInd")
X["M5r_transit_access"] = wmean("D5BR0") / 1000
note("M5r_transit_access", "Population-weighted mean of SLD D5br over block groups inside the city: thousands of jobs reachable within a 45-minute transit commute (walk + scheduled transit, distance-decay, TravelTime API 2020 with 2017 jobs); block groups with no transit within walking distance count as 0")
share = lambda flag: (flag * bg.TotPop).groupby(bg.city_id).sum() / bg.TotPop.groupby(bg.city_id).sum()
cov = pd.DataFrame({"pop_share_no_frequency_D4c": share(bg.D4C < 0), "pop_share_no_stop_within_1200m_D4a": share(bg.D4A < 0)})
cov.round(3).to_csv(OUT / "audit_sld_transit_coverage.csv")
nofreq = cov[cov.pop_share_no_frequency_D4c - cov.pop_share_no_stop_within_1200m_D4a > 0.25].index   # stops exist but no frequency data
X.loc[nofreq, "M1_transit_frequency"] = np.nan

ntd = pd.read_csv(D / "extracted/mobility_opportunities/ntd_associated_provider_service_2022_2025.csv", dtype=str)
tonum = lambda col: pd.to_numeric(ntd[col].str.replace(",", ""), errors="coerce")
ntd["rh"], ntd["sap"] = tonum("Actual Vehicle/Passenger Car Revenue Hours"), tonum("Service Area Population")
fx = ntd[~ntd.Mode.isin(["DR", "DT", "VP"])]          # fixed-route modes; demand response and vanpool excluded
th = fx.pivot_table(index=["city_id", "Report Year"], columns="Time Period", values="rh", aggfunc="sum")
hpc = (th["Annual Total"] / fx.groupby(["city_id", "Report Year"]).sap.first()).unstack()
X["M1r_transit_hours_pc"], S["M1r_transit_hours_pc"] = hpc.mean(axis=1), hpc.std(axis=1, ddof=1) / 2
wkd = ((th["Average Typical Saturday"] + th["Average Typical Sunday"]) / 2 / th["Average Typical Weekday"]).unstack()
X["M4r_weekend_retention"], S["M4r_weekend_retention"] = wkd.mean(axis=1), wkd.std(axis=1, ddof=1) / 2
note("M1r_transit_hours_pc", "Annual fixed-route vehicle revenue hours of the principal operator per resident of its service area, NTD 2022-2025 mean (rail cars counted individually)")
note("M4r_weekend_retention", "Mean of typical Saturday and Sunday revenue hours divided by typical weekday revenue hours, principal operator, NTD 2022-2025 mean")
note("M1_transit_frequency", f"Missing for {list(nofreq)}: SLD has stops but no frequency data there. Population-weighted mean of SLD D4c (transit trips per hour within 0.25 mile, weekday evening peak) over block groups inside the city; unserved block groups count as 0; SLD v3 (GTFS around 2020)")
note("M2_walkability", "Population-weighted mean National Walkability Index (1-20) over block groups inside the city, SLD v3")

fare = pd.read_csv(D / "extracted/policy_parameters/youth_transit_policies_25cities.csv", dtype=str).set_index("city_id")
X["M3_youth_fare"] = fare.value.astype(float)
note("M3_youth_fare", "Fare in USD paid by an eligible high-school student for one local ride on the principal operator (0 = free); Dallas and Indianapolis values are 3-hour and 2-hour passes")

# ---------- activities ----------
X["A1_park_access"] = obs[obs.source_id == "S19"].set_index("city_id").v
S["A1_park_access"] = 0.3
note("A1_park_access", "Percent of residents within a 10-minute walk of a park, TPL; Charlotte and Nashville are county-scale, three cities have unconfirmed measurement year; SD 0.3 for rounding")

lib = obs[obs.source_id.isin(["S20", "S20-state"]) & obs.indicator_id.isin(["imls_yaatten", "imls_popu_lsa"])].copy()
lib["fy"] = lib.observation_period.str[:6]
lw = lib.pivot_table(index=["city_id", "fy", "source_id", "source_geo_id"], columns="indicator_id", values="v")
fed = lw.xs("S20", level="source_id").dropna()
ya = (fed.imls_yaatten.groupby(level=[0, 1]).sum() / fed.imls_popu_lsa.groupby(level=[0, 1]).sum() * 1000).unstack()
fw_att = lw.xs("S20-state", level="source_id").loc["4827000"].imls_yaatten.dropna().iloc[0]
fw_pop = lw.xs("S20", level="source_id").loc["4827000"].imls_popu_lsa.dropna().iloc[0]
ya.loc["4827000", "FY2024"] = fw_att / fw_pop * 1000
X["A2_library_teen"] = ya.mean(axis=1)
S["A2_library_teen"] = ya.std(axis=1, ddof=1) / np.sqrt(ya.notna().sum(axis=1))
note("A2_library_teen", "Young-adult library programme attendance per 1,000 service-area residents, IMLS FY2023-FY2024 mean over associated systems; Fort Worth from the Texas FY2024 state table")

rpp = pd.read_csv(D / "extracted/foundation/costs/city_observations.csv", dtype=str)
rpp["v"] = pd.to_numeric(rpp.value, errors="coerce")
r24 = rpp[rpp.observation_period == "2024"].pivot_table(index="city_id", columns="indicator_id", values="v")
wage = pd.read_csv(P / "supplement_20261111/wages/city_youth_wage_rules_25cities.csv", dtype=str).set_index("city_id")
X["A4_teen_wage_real"] = wage.age_16_17_reference_rate.astype(float) / (r24.MARPP_1 / 100)
note("A4_teen_wage_real", "Statutory minimum hourly wage for a 16-17-year-old in an ordinary covered job (as of 2026-11-11), divided by the 2024 BEA all-items regional price parity")

# ---------- affordability ----------
fm = obs[(obs.source_id == "S22") & (obs.indicator_id == "hud_fmr_2br") & (obs.observation_period == "FY2024")].copy()
fm["county_id"] = fm.source_geo_id.str.split("|").str[-1]
cw = pd.read_csv(D / "metadata/city_county_crosswalk.csv", dtype=str)
fm = fm.merge(cw[["city_id", "county_id", "city_population_share_2024"]], on=["city_id", "county_id"], how="left")
fm["w"] = fm.city_population_share_2024.astype(float).fillna(1.0)   # Boston town-level HUD area has no county share row
X["C1_rent_2br"] = (fm.v * fm.w).groupby(fm.city_id).sum() / fm.w.groupby(fm.city_id).sum()
note("C1_rent_2br", "HUD FY2024 two-bedroom Fair Market Rent, USD per month, weighted by the city's residents in each county; a rent standard for the HUD area, not observed city rent")
X["C2_nonhousing_prices"] = (r24.MARPP_2 + r24.MARPP_5) / 2
note("C2_nonhousing_prices", "Mean of BEA 2024 regional price parities for goods and for other services (US = 100), MSA level; housing and utilities excluded to avoid overlap with C1")

# ---------- inclusion ----------
h = obs[obs.source_id == "S23"].pivot_table(index="city_id", columns="indicator_id", values="v")
X["I1_equality_policy"] = (h.MEI_nondiscrimination_score + h.MEI_municipal_services_score) / 42 * 100
note("I1_equality_policy", "HRC MEI 2025 parts I (non-discrimination laws, 30) and III (municipal services, 12) as percent of 42; Washington DC is not rated and stays missing")

X = X.reindex(CID)
S = S.reindex(CID).reindex(columns=X.columns)
X.insert(0, "city", cities.set_index("city_id").city_name.str.replace(r" city.*| metropolitan.*", "", regex=True))
X.to_csv(OUT / "indicator_matrix.csv", index_label="city_id")
S.to_csv(OUT / "indicator_sd.csv", index_label="city_id")
pd.DataFrame(notes).to_csv(OUT / "indicator_notes.csv", index=False)
pd.set_option("display.width", 250)
print(X.round(2).to_string())
print(X.drop(columns="city").describe().loc[["min", "50%", "max"]].round(2).T.to_string())
print("missing:", X.isna().sum()[X.isna().sum() > 0].to_dict())
