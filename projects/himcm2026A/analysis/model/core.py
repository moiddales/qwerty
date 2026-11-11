"""Model definitions shared by all computations: indicators, fixed reference nodes, preference set, solvers.

All reference nodes are absolute values fixed before any score was computed; they do not depend on the candidate cities.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog

P = Path(__file__).resolve().parents[2]
RES = P / "results"

DOMAINS = ["Education", "Safety", "Health", "Mobility", "Activities", "Affordability", "Inclusion"]

# indicator: (domain, [worst, node1, node2, best], basis of the nodes)
SPEC_M0 = {
    "E1_adv_course":          ("Education", [10, 25, 40, 55], "course enrolments per 100 students; equal steps"),
    "E2_grad_rate":           ("Education", [60, 75, 85, 95], "four-year graduation rate, percent"),
    "E3_counselors":          ("Education", [2, 3, 4, 6], "4 per 1,000 is the ASCA-recommended 250:1 ratio"),
    "S1_violent_crime":       ("Safety", [1200, 900, 600, 300], "violent crimes per 100,000; worst node is also the reference floor"),
    "S2_traffic_deaths":      ("Safety", [20, 14, 8, 2], "traffic deaths per 100,000; worst node is also the reference floor"),
    "H1_bad_air_days":        ("Health", [30, 15, 5, 0], "percent of days with AQI above 100 (EPA 'unhealthy for sensitive groups' or worse)"),
    "H2_school_health_staff": ("Health", [0.5, 2, 4, 8], "nurses+psychologists+social workers per 1,000 students"),
    "H3_youth_mh_facilities": ("Health", [2, 6, 12, 20], "listed youth mental-health facilities per 100,000 under 18"),
    "M1_transit_frequency":   ("Mobility", [0, 5, 20, 60], "evening-peak transit trips per hour near home (SLD D4c)"),
    "M2_walkability":         ("Mobility", [5.75, 10.5, 15.25, 20], "EPA National Walkability Index category boundaries"),
    "M3_youth_fare":          ("Mobility", [2.0, 1.0, 0.5, 0.0], "USD per ride; 0 = free"),
    "A1_park_access":         ("Activities", [30, 55, 80, 100], "percent of residents within a 10-minute walk of a park"),
    "A2_library_teen":        ("Activities", [0, 10, 25, 50], "teen library programme attendance per 1,000 residents"),
    "A3_school_sports":       ("Activities", [10, 20, 35, 50], "school sports participations per 100 students"),
    "A4_teen_wage_real":      ("Activities", [6.5, 10, 14, 18], "price-adjusted minimum hourly wage for ages 16-17, USD"),
    "C1_rent_share":          ("Affordability", [50, 40, 30, 15], "2-bedroom rent as percent of reference income; 30 = HUD affordability standard, 50 = HUD severe burden (reference floor)"),
    "C2_nonhousing_prices":   ("Affordability", [110, 105, 100, 95], "BEA price parity for goods and other services, US = 100"),
    "I1_equality_policy":     ("Inclusion", [25, 50, 75, 100], "percent of MEI parts I and III"),
    "I2_suspension":          ("Inclusion", [16, 10, 5, 0], "students suspended out of school per 100"),
}
# M1 revision: replace the SLD frequency proxy and the school-location graduation measure, add weekend service
SPEC_M1 = {k: v for k, v in SPEC_M0.items() if k not in ("M1_transit_frequency", "E2_grad_rate")}
SPEC_M1.update({
    "E2r_grad_district":     ("Education", [60, 75, 85, 95], "four-year graduation rate of non-charter schools, percent"),
    "M1r_transit_hours_pc":  ("Mobility", [0.25, 0.75, 1.5, 3.0], "annual fixed-route revenue hours per service-area resident"),
    "M4r_weekend_retention": ("Mobility", [0.3, 0.5, 0.7, 0.9], "weekend service hours as a share of weekday hours"),
})

REF_INCOME = 80000          # USD per year, reference household scenario
FLOORS = {"C1_rent_share": 50.0, "S1_violent_crime": 1200.0, "S2_traffic_deaths": 20.0, "H1_bad_air_days": 30.0}
SEG_SHAPE = np.array([0.5628, 0.2888, 0.1484])   # exponential value function with k = 2 evaluated at z = 1/3, 2/3, 1
DOM_LO, DOM_HI = 1 / 14, 2 / 7                    # each domain between half and double the equal share
IND_MIN_FRAC = 1 / 3                              # an indicator carries at least 1/3 of the equal share within its domain
LAST_SEG_MIN = 0.10                               # the last segment keeps at least 10% of its indicator's value


def load(income=REF_INCOME):
    X = pd.read_csv(RES / "indicator_matrix.csv", dtype={"city_id": str}).set_index("city_id")
    S = pd.read_csv(RES / "indicator_sd.csv", dtype={"city_id": str}).set_index("city_id")
    names = X.pop("city")
    X["C1_rent_share"] = X.C1_rent_2br * 12 / income * 100
    S["C1_rent_share"] = 0.0
    return names, X, S.reindex(columns=X.columns).fillna(0.0)


class Model:
    def __init__(self, spec):
        self.spec = spec
        self.inds = list(spec)
        self.m = len(self.inds)
        self.dom = [spec[i][0] for i in self.inds]
        self.nodes = np.array([spec[i][1] for i in self.inds], float)
        self.n = 3 * self.m
        self.theta0 = self._theta0()
        self.A_ub, self.b_ub, self.A_eq, self.b_eq = self._constraints()

    def _theta0(self):
        th = np.zeros(self.n)
        for j, d in enumerate(self.dom):
            th[3 * j:3 * j + 3] = SEG_SHAPE / len(DOMAINS) / self.dom.count(d)
        return th

    def phi(self, x):
        """Segment coverage for a matrix of raw values (cities x indicators), shape (cities, 3m)."""
        x = np.asarray(x, float)
        t = self.nodes
        cov = (x[:, :, None] - t[None, :, :3]) / (t[None, :, 1:] - t[None, :, :3])
        return np.clip(cov, 0, 1).reshape(len(x), -1)

    def _constraints(self):
        A, b = [], []
        row = lambda: np.zeros(self.n)
        for j in range(self.m):
            s = 3 * j
            for l in (0, 1):                       # concavity: theta_l >= theta_{l+1}
                r = row(); r[s + l] = -1; r[s + l + 1] = 1; A.append(r); b.append(0)
            r = row(); r[s:s + 3] = LAST_SEG_MIN; r[s + 2] -= 1; A.append(r); b.append(0)
        for d in DOMAINS:
            idx = [j for j in range(self.m) if self.dom[j] == d]
            dom = row()
            for j in idx:
                dom[3 * j:3 * j + 3] = 1
            A.append(dom); b.append(DOM_HI)
            A.append(-dom); b.append(-DOM_LO)
            for j in idx:                          # indicator total >= IND_MIN_FRAC * domain total / n_d
                r = dom * IND_MIN_FRAC / len(idx); r[3 * j:3 * j + 3] -= 1; A.append(r); b.append(0)
        return np.array(A), np.array(b), np.ones((1, self.n)), np.array([1.0])

    def lp(self, c, extra_A=None, extra_b=None, nvar_extra=0):
        """Minimise c'theta over the preference set; optional extra rows and extra free variables."""
        A, b, Ae = self.A_ub, self.b_ub, self.A_eq
        if nvar_extra:
            A = np.hstack([A, np.zeros((len(A), nvar_extra))]); Ae = np.hstack([Ae, np.zeros((1, nvar_extra))])
        if extra_A is not None:
            A = np.vstack([A, extra_A]); b = np.concatenate([b, extra_b])
        bounds = [(0, None)] * self.n + [(None, None)] * nvar_extra
        r = linprog(c, A_ub=A, b_ub=b, A_eq=Ae, b_eq=self.b_eq, bounds=bounds, method="highs")
        if r.status != 0:
            raise RuntimeError(r.message)
        return r

    def feasible(self, th):
        return bool(np.all(self.A_ub @ th <= self.b_ub + 1e-9) and abs(th.sum() - 1) < 1e-9 and np.all(th >= -1e-12))

    def sample_theta(self, n, rng, centre=None, conc=None):
        """Draw preference vectors from the set. centre=None: flat Dirichlet with rejection.
        centre = dict domain->share with concentration conc: Dirichlet centred on that profile."""
        out = []
        nd = len(DOMAINS)
        alpha = np.ones(nd) if centre is None else conc * np.array([centre[d] for d in DOMAINS])
        got = 0
        while got < n:
            w = rng.dirichlet(alpha, size=4 * n)
            w = w[(w.min(1) >= DOM_LO) & (w.max(1) <= DOM_HI)][:n - got]
            got += len(w)
            th = np.zeros((len(w), self.n))
            for k, d in enumerate(DOMAINS):
                idx = [j for j in range(self.m) if self.dom[j] == d]
                share = np.empty((len(w), len(idx)))
                todo = np.ones(len(w), bool)
                while todo.any():
                    s = rng.dirichlet(np.ones(len(idx)), size=todo.sum())
                    ok = s.min(1) >= IND_MIN_FRAC / len(idx)
                    rows = np.flatnonzero(todo)[ok]
                    share[rows] = s[ok]; todo[rows] = False
                for a, j in enumerate(idx):
                    seg = np.empty((len(w), 3))
                    todo = np.ones(len(w), bool)
                    while todo.any():
                        g = -np.sort(-rng.dirichlet(np.ones(3), size=todo.sum()), axis=1)
                        ok = g[:, 2] >= LAST_SEG_MIN
                        rows = np.flatnonzero(todo)[ok]
                        seg[rows] = g[ok]; todo[rows] = False
                    th[:, 3 * j:3 * j + 3] = seg * (w[:, k] * share[:, a])[:, None]
            out.append(th)
        return np.vstack(out)[:n]


def fill_missing(X, how="median"):
    """Reference treatment of a missing indicator value. 'median' = median of the cities that have data."""
    X = X.copy()
    for c in X.columns[X.isna().any()]:
        X[c] = X[c].fillna(X[c].median())
    return X


def ranks(u):
    """Rank 1 = best; u is (..., cities)."""
    return (-u).argsort(axis=-1).argsort(axis=-1) + 1
