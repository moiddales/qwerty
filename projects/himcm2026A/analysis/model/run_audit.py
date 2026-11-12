"""Logic audit of the final model: checks behind statements in paper Sections 6.4, 8.1 and 8.3.

    cd projects/himcm2026A/analysis/model && python run_audit.py > ../../results/logic_audit.txt

Part A (seed 42): Theta_S with San Francisco excluded; pool independence of the mean-rank order; P1 and P2 removed together;
teen wage deflated by non-housing prices. Part B (seed 7): node shifts and leave-one-measure-out under Theta_S.
Part C (seeds 11, 12): the non-charter rule applied to all five CRDC school measures (needs data/extracted).
Part D (seed 21): mean vector of Theta_S, central weights and confidence factors, joint affordable-and-accessible measure.
Part E: pool independence with the median fill recomputed, Seattle's regret rivals, domain weights fixed at 1/7.
"""
import numpy as np, pandas as pd
from core import *
rng=np.random.default_rng(42)
names,X,S=load(); CITY=names.values; nC=len(CITY)
def noisy_U(M, th, X=X):
    x=X[M.inds].values.astype(float); s=S[M.inds].values.astype(float); out=[]
    for a in range(0,len(th),500):
        k=min(500,len(th)-a); d=x[None]+rng.standard_normal((k,)+x.shape)*s[None]
        for j in range(M.m):
            miss=np.isnan(x[:,j])
            if miss.any(): d[:,miss,j]=rng.choice(x[~miss,j],size=(k,miss.sum()))
        out.append(np.einsum("nck,nk->nc",M.phi(d.reshape(-1,M.m)).reshape(k,nC,M.n),th[a:a+k]))
    return np.vstack(out)
def top(U,mask=None,n=5):
    idx=np.arange(nC) if mask is None else np.flatnonzero(mask)
    r=ranks(U[:,idx]); t=pd.DataFrame({'city':CITY[idx],'p1':(r==1).mean(0),'top3':(r<=3).mean(0),'mr':r.mean(0)}).sort_values('mr')
    return t.head(n).round(3).to_string(index=False)
MP=Model(SPEC_M2,STATEMENTS_PLAN); th=MP.sample_theta(10000,rng); U=noisy_U(MP,th)
print("Theta_S all cities\n",top(U))
fl=pd.read_csv('../../results/floors_status.csv',dtype={'city_id':str},index_col=0).reindex(names.index)
print("Theta_S excluding floor-fail\n",top(U,(fl.status!='fail').values))
# pool dependence of mean-rank order
r=ranks(U); mr=r.mean(0); base=np.argsort(mr); rev=0; changed=[]
for c in range(nC):
    keep=[i for i in range(nC) if i!=c]; m2=ranks(U[:,keep]).mean(0)
    o1=mr[keep]; 
    for a in range(len(keep)):
        for b in range(a+1,len(keep)):
            if (o1[a]-o1[b])*(m2[a]-m2[b])<0: rev+=1; changed.append((CITY[c],CITY[keep[a]],CITY[keep[b]]))
    w=ranks(U[:,keep])==1
print("mean-rank pair reversals over 25 removals:",rev, changed[:8])
# P1 and P2 removed together
M35=Model(SPEC_M2,[s for s in STATEMENTS_PLAN if s['id'] not in('P1','P2')]); th35=M35.sample_theta(10000,rng)
print("Theta without P1,P2\n",top(noisy_U(M35,th35)))
# affordability weight in Theta_S draws vs winner
aff=th[:,[3*j+l for j in range(MP.m) if MP.dom[j]=='Affordability' for l in range(3)]].sum(1)
w=ranks(U)[:, list(CITY).index('Seattle')]==1
print("aff weight: mean %.3f, share draws aff<1/7 %.3f; Seattle wins when aff<1/7: %.3f, aff>=1/7: %.3f"%(aff.mean(),(aff<1/7).mean(),w[aff<1/7].mean(),w[aff>=1/7].mean()))
# alternative wage deflator (non-housing prices)
P=RES.parent; D=P/'data'
rpp=pd.read_csv(D/"extracted/foundation/costs/city_observations.csv",dtype=str); rpp["v"]=pd.to_numeric(rpp.value,errors="coerce")
r24=rpp[rpp.observation_period=="2024"].pivot_table(index="city_id",columns="indicator_id",values="v")
wage=pd.read_csv(P/"supplement_20261111/wages/city_youth_wage_rules_25cities.csv",dtype=str).set_index("city_id")
X2=X.copy(); X2["A4_teen_wage_real"]=wage.age_16_17_reference_rate.astype(float)/(X.C2_nonhousing_prices/100)
print(pd.DataFrame({'city':CITY,'allitems':X.A4_teen_wage_real.round(2),'nonhousing':X2.A4_teen_wage_real.round(2)}).sort_values('nonhousing',ascending=False).head(8).to_string(index=False))
Mr=Model(SPEC_M2); U0=Mr.phi(fill_missing(X2[Mr.inds]).values)@Mr.theta0
print("ref top5 alt deflator:",[ (CITY[i],round(U0[i],4)) for i in np.argsort(-U0)[:5]])
print("Theta_S alt deflator\n",top(noisy_U(MP,th,X2)))

# ================================================================ part B
rng=np.random.default_rng(7)   # part B: tests under Theta_S on point data
names,X,S=load(); CITY=names.values
MP=Model(SPEC_M2,STATEMENTS_PLAN); th=MP.sample_theta(4000,rng); Xr=fill_missing(X[MP.inds])
PH=MP.phi(Xr.values); base=ranks(th@PH.T)
def lead(r): p=(r==1).mean(0); o=np.argsort(-p)[:3]; return "; ".join(f"{CITY[i]} {p[i]:.3f}" for i in o)
print("Theta_S point data:",lead(base))
# node shifts +-10% under Theta_S
R=[]
for t in th[:2000]:
    sp={}
    for k,(dm,nd,why) in MP.spec.items():
        nd=np.array(nd,float); span=nd[3]-nd[0]; nd2=nd+rng.uniform(-.1,.1,4)*span
        sp[k]=(dm,list(np.sort(nd2) if span>0 else -np.sort(-nd2)),why)
    m2=Model(sp); R.append(ranks(m2.phi(Xr.values)@t))
print("Theta_S + node shifts:",lead(np.array(R)))
# leave one measure out, domain weight kept
out=[]
for j,ind in enumerate(MP.inds):
    t=th.copy(); d=MP.dom[j]; same=[k for k in range(MP.m) if MP.dom[k]==d and k!=j]
    dt=t.reshape(len(t),MP.m,3); tot=dt[:,[k for k in range(MP.m) if MP.dom[k]==d]].sum((1,2))
    dt[:,j]=0; rest=dt[:,same].sum((1,2)); dt[:,same]*= (tot/rest)[:,None,None]
    r=ranks(dt.reshape(len(t),-1)@PH.T); p=(r==1).mean(0); out.append((ind,CITY[p.argmax()],round(p.max(),3),round(p[list(CITY).index('Seattle')],3)))
o=pd.DataFrame(out,columns=['dropped','leader','p','p_Seattle']); print(o.to_string(index=False)); print(o.leader.value_counts().to_dict())

# ================================================================ part C: Revision 1's non-charter rule applied to all five CRDC school measures
def noisy_U2(M, th, X, rng):
    x = X[M.inds].values.astype(float); s = S.reindex(columns=M.inds).fillna(0).values.astype(float); out = []
    for a in range(0, len(th), 500):
        k = min(500, len(th) - a); d = x[None] + rng.standard_normal((k,) + x.shape) * s[None]
        for j in range(M.m):
            miss = np.isnan(x[:, j])
            if miss.any(): d[:, miss, j] = rng.choice(x[~miss, j], size=(k, miss.sum()))
        out.append(np.einsum("nck,nk->nc", M.phi(d.reshape(-1, M.m)).reshape(k, nC, M.n), th[a:a + k]))
    return np.vstack(out)


def rep(U, n=5):
    r = ranks(U); t = pd.DataFrame({'city': CITY, 'p1': (r == 1).mean(0), 'top3': (r <= 3).mean(0), 'mr': r.mean(0)}).sort_values('mr')
    return t.head(n).round(3).to_string(index=False)


CR = RES.parent / 'data/extracted/education_inclusion/crdc_2324/SCH'
rd = lambda f: pd.read_csv(CR / f'{f}.csv', dtype=str)
def num(df, cols):
    v = df[cols].apply(pd.to_numeric, errors='coerce'); return v.where(v >= 0).sum(axis=1, min_count=1)
ch = rd('School_Characteristics'); enr = rd('Enrollment')
base = enr[['city_id', 'COMBOKEY']].copy(); base['enr'] = num(enr, ['TOT_ENR_M', 'TOT_ENR_F'])
base = base.merge(ch[['COMBOKEY', 'SCH_STATUS_CHARTER', 'SCH_STATUS_ALT']], on='COMBOKEY', how='left')
oss = [f"TOT_DISC{w}_{k}OOS{i}_{g}" for w, i in (("WODIS", ""), ("WDIS", "_IDEA")) for k in ("SING", "MULT") for g in "MF"]
for f, cols, name in [('Advanced_Placement', ['TOT_APENR_M', 'TOT_APENR_F'], 'ap'), ('International_Baccalaureate', ['TOT_IBENR_M', 'TOT_IBENR_F'], 'ib'),
                      ('Dual_Enrollment', ['TOT_DUALENR_M', 'TOT_DUALENR_F'], 'dual'), ('School_Support', ['SCH_FTECOUNSELORS'], 'coun'),
                      ('School_Support', ['SCH_FTESERVICES_NUR', 'SCH_FTESERVICES_PSY', 'SCH_FTESERVICES_SOC'], 'hs'),
                      ('Interscholastic_Athletics', ['TOT_PART'], 'ath'), ('Suspensions', oss, 'oss')]:
    d = rd(f); d[name] = num(d, cols); base = base.merge(d[['COMBOKEY', name]], on='COMBOKEY', how='left')
def rates(b):
    g = b.groupby('city_id'); e = g.enr.sum()
    return pd.DataFrame({'E1_adv_course': (g.ap.sum() + g.ib.sum() + g.dual.sum()) / e * 100, 'E3_counselors': g.coun.sum() / e * 1000,
                         'H2_school_health_staff': g.hs.sum() / e * 1000, 'A3_school_sports': g.ath.sum() / e * 100, 'I2_suspension': g.oss.sum() / e * 100})
cs = (base[base.SCH_STATUS_CHARTER == 'Yes'].groupby('city_id').enr.sum() / base.groupby('city_id').enr.sum()).reindex(X.index)
print("\ncharter share of enrolment:", {c: round(float(cs.iloc[list(CITY).index(c)]), 3) for c in ('Seattle', 'Denver', 'Chicago', 'New York')}, "max", CITY[cs.values.argmax()], round(float(cs.max()), 3))
MR = Model(SPEC_M2); thC = MP.sample_theta(10000, np.random.default_rng(11))
for tag, b in (('non-charter', base[base.SCH_STATUS_CHARTER == 'No']), ('non-charter, non-alternative', base[(base.SCH_STATUS_CHARTER == 'No') & (base.SCH_STATUS_ALT != 'Yes')])):
    nc = rates(b); Xc = X.copy()
    for c in nc.columns: Xc[c] = nc[c].reindex(X.index)
    Xc.loc[X.A3_school_sports.isna(), 'A3_school_sports'] = np.nan
    u = MR.phi(fill_missing(Xc[MR.inds]).values) @ MR.theta0
    print(tag, "ref top5:", [(CITY[i], round(float(u[i]), 4)) for i in np.argsort(-u)[:5]])
    print(rep(noisy_U2(MP, thC, Xc, np.random.default_rng(12))))

# ================================================================ part D: one transparent vector for Theta_S, confidence factors, joint measure
ix = {c: i for i, c in enumerate(CITY)}
def domw(M, t):
    w = t.reshape(M.m, 3).sum(1); return {d: round(float(sum(w[j] for j in range(M.m) if M.dom[j] == d)), 3) for d in DOMAINS}
rng = np.random.default_rng(21)
thD = MP.sample_theta(10000, rng); rD = ranks(noisy_U2(MP, thD, X, rng))
PHD = MP.phi(fill_missing(X[MP.inds]).values); tm = thD.mean(0); u = PHD @ tm
print("\nmean vector of Theta_S, domain weights:", domw(MP, tm))
print("U at mean vector:", [(CITY[i], round(float(u[i]), 4)) for i in np.argsort(-u)[:6]])
for c in ('Seattle', 'Denver', 'Chicago', 'New York'):
    cw = thD[rD[:, ix[c]] == 1].mean(0); rr = ranks(noisy_U2(MP, np.repeat(cw[None], 5000, 0), X, rng))
    print(c, "central weights:", domw(MP, cw), "confidence factor:", round(float((rr[:, ix[c]] == 1).mean()), 3))
jf = pd.read_csv(RES / 'joint_feasibility_tracts.csv', dtype={'city_id': str}, index_col=0).reindex(X.index)
spec = {k: v for k, v in SPEC_M2.items() if k != "M5r_transit_access"}
spec["M5j_affordable_access_share"] = ("Mobility", [0.02, 0.10, 0.30, 0.60], "")
Xj = X.copy(); Xj["M5j_affordable_access_share"] = jf["share_affordable_and_access60k_80k"].values
mj = Model(spec, STATEMENTS_PLAN)
print("joint affordable+accessible share replaces access, Theta_S\n", rep(noisy_U2(mj, mj.sample_theta(10000, rng), Xj, rng)))

# ================================================================ part E: exact checks
import core
Xm = X[MR.inds]; Uref = MR.phi(fill_missing(Xm).values) @ MR.theta0; n = 0
for d in range(nC):                      # leave one city out, recomputing the median fill of missing cells
    keep = [i for i in range(nC) if i != d]; u = MR.phi(fill_missing(Xm.iloc[keep]).values) @ MR.theta0; b = Uref[keep]
    n += int(((b[:, None] > b[None, :]) & (u[:, None] < u[None, :])).sum())
print("\nreference-score pair reversals with the median fill recomputed:", n)
i = ix['Seattle']; dd = {CITY[k]: round(-MP.lp(-(PHD[k] - PHD[i])).fun, 4) for k in range(nC) if k != i}
print("Seattle's largest possible losses under Theta_S:", sorted(dd.items(), key=lambda t: -t[1])[:3])
core.DOM_LO, core.DOM_HI = 1 / 7 - 1e-9, 1 / 7 + 1e-9
mf = Model(SPEC_M2); PF = mf.phi(fill_missing(X[mf.inds]).values)
print("necessary pairs with every domain weight fixed at 1/7 and the split inside domains free:",
      sum(1 for a in range(nC) for b in range(nC) if a != b and mf.lp(PF[a] - PF[b]).fun >= 0))
