"""Logic audit of the final model: checks behind statements in paper Sections 6.4, 8.1 and 8.3.

    cd projects/himcm2026A/analysis/model && python run_audit.py > ../../results/logic_audit.txt

Part A (seed 42): Theta_S with San Francisco excluded; pool independence of the mean-rank order; P1 and P2 removed together;
teen wage deflated by non-housing prices. Part B (seed 7): node shifts and leave-one-measure-out under Theta_S.
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
