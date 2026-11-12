"""Checks for the user checklist of 2026-11-12: reference-only tests repeated under Theta_S, safety-weight statements,
weighted CES under Theta_S, Chicago crime definition under Theta_S.

    cd projects/himcm2026A/analysis/model && python run_checklist_checks.py
"""
import numpy as np, pandas as pd, json, sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from core import *
names,X,S=load(); C=list(names.values); nC=len(C); RESP=RES.parent
def U(M,th,X,S,rng):
    x=X[M.inds].values.astype(float); s=S.reindex(columns=M.inds).fillna(0).values.astype(float); out=[]
    for a in range(0,len(th),500):
        k=min(500,len(th)-a); d=x[None]+rng.standard_normal((k,)+x.shape)*s[None]
        for j in range(M.m):
            m=np.isnan(x[:,j])
            if m.any(): d[:,m,j]=rng.choice(x[~m,j],size=(k,m.sum()))
        out.append(np.einsum("nck,nk->nc",M.phi(d.reshape(-1,M.m)).reshape(k,nC,M.n),th[a:a+k]))
    return np.vstack(out)
def top(Uv,n=4):
    r=ranks(Uv); p=(r==1).mean(0); o=np.argsort(r.mean(0))[:n]
    return "; ".join(f"{C[i]} {p[i]*100:.1f}% (mean rank {r.mean(0)[i]:.2f})" for i in o)
OUT={}
MP=Model(SPEC_M2,STATEMENTS_PLAN); th=MP.sample_theta(10000,np.random.default_rng(42))
OUT['baseline']=top(U(MP,th,X,S,np.random.default_rng(1)))
for k in (2,4): OUT[f'sd_x{k}']=top(U(MP,th,X,S*k,np.random.default_rng(1)))
# domain weights under Theta_S
W=th.reshape(len(th),MP.m,3).sum(2); dw={d:W[:,[j for j in range(MP.m) if MP.dom[j]==d]].sum(1) for d in DOMAINS}
OUT['domain_weight_mean']={d:round(float(v.mean()),3) for d,v in dw.items()}
OUT['share_safety_below_1_7']=round(float((dw['Safety']<1/7).mean()),3)
OUT['share_safety_lowest_domain']=round(float(np.mean(np.argmin(np.stack([dw[d] for d in DOMAINS],1),1)==DOMAINS.index('Safety'))),3)
# Chicago crime CPD definition
pop21=pd.read_csv(RESP/"data/extracted/foundation/population_25cities_2020_2025.csv",dtype=str).set_index("city_id").POPESTIMATE2021.astype(float)
Xc=X.copy(); Xc.loc["1714000","S1_violent_crime"]=25979/pop21["1714000"]*1e5
OUT['chicago_crime_960']=top(U(MP,th,Xc,S,np.random.default_rng(1)))
# metro (CBSA) air
aq=pd.read_csv(RESP/"data/processed/observations_all_levels.csv.gz",dtype=str,low_memory=False,usecols=["source_id","indicator_id","value","observation_period","city_id","geography_type"])
aq=aq[(aq.source_id=="S10")&(aq.geography_type=="CBSA")]; aq["v"]=pd.to_numeric(aq.value)
w=aq.pivot_table(index=["city_id","observation_period"],columns="indicator_id",values="v")
bad=["cbsa_aqi_unhealthy_for_sensitive_groups_days","cbsa_aqi_unhealthy_days","cbsa_aqi_very_unhealthy_days","cbsa_aqi_hazardous_days"]
cb=(w[bad].sum(axis=1)/w.cbsa_aqi_days_with_aqi*100).groupby(level=0).mean().reindex(X.index)
Xa=X.copy(); Xa["H1_bad_air_days"]=cb.values
OUT['metro_air']=top(U(MP,th,Xa,S,np.random.default_rng(1)))
# Poisson-Gamma teen traffic
pg=pd.read_csv(RES/"poisson_gamma_teen_traffic.csv",dtype={"city_id":str},index_col=0).reindex(X.index)
spec={k:v for k,v in SPEC_M2.items() if k!="S2_traffic_deaths"}; spec["S2r_teen_traffic_eb"]=("Safety",[12,8,5,2],"")
Xp=X.copy(); Xp["S2r_teen_traffic_eb"]=pg.eb_per_100k.values
mp=Model(spec,STATEMENTS_PLAN); thp=mp.sample_theta(10000,np.random.default_rng(42))
OUT['teen_traffic_PG']=top(U(mp,thp,Xp,S,np.random.default_rng(1)))
# extra safety statements
extra={'safety_ge_1_7':[{"id":"P6","type":"domain_min","a":"Safety","value":1/7}],
       'safety_ge_every_domain':[{"id":f"P6{d}","type":"domain_ge","a":"Safety","b":d} for d in DOMAINS if d!="Safety"]}
for k,st in extra.items():
    m=Model(SPEC_M2,STATEMENTS_PLAN+st); t=m.sample_theta(10000,np.random.default_rng(42))
    OUT[k]=top(U(m,t,X,S,np.random.default_rng(1)))
    Wk=t.reshape(len(t),m.m,3).sum(2); OUT[k+'_mean_safety_w']=round(float(Wk[:,[j for j in range(m.m) if m.dom[j]=='Safety']].sum(1).mean()),3)
# weighted CES across domains with Theta_S weights
PH=MP.phi(fill_missing(X[MP.inds]).values)
contrib=(PH[None]*th[:,None,:]).reshape(len(th),nC,MP.m,3).sum(3)
for rho in (0,-1):
    sc=[]
    for d in DOMAINS:
        idx=[j for j in range(MP.m) if MP.dom[j]==d]; sc.append(contrib[:,:,idx].sum(2)/dw[d][:,None])
    s=np.clip(np.stack(sc,2),1e-6,1); wd=np.stack([dw[d] for d in DOMAINS],1)[:,None,:]
    val=np.exp((wd*np.log(s)).sum(2)) if rho==0 else ((wd*s**rho).sum(2))**(1/rho)
    OUT[f'ces_rho{rho}_thetaS_point']=top(val)
json.dump(OUT,open(RES / 'checklist_checks.json', 'w'),indent=1)
print(json.dumps(OUT,indent=1))
