"""Precision of Table 1: standard error of each neighbouring mean-rank gap (same draws as run_preferences.py, seed 42),
and Theta_S leaders when graduation or advanced courses are removed (point data, seed 7 as in run_audit.py part B).

    cd projects/himcm2026A/analysis/model && python run_table1_precision.py
"""
import json
import numpy as np, pandas as pd, sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from core import *
names,X,S=load(); C=list(names.values); nC=len(C)
rng=np.random.default_rng(42)
MP=Model(SPEC_M2,STATEMENTS_PLAN)
def noisy_U(M, thetas):
    x = X[M.inds].values.astype(float); s = S[M.inds].values.astype(float); n=len(thetas); out=[]
    for a in range(0, n, 500):
        k = min(500, n - a); d = x[None] + rng.standard_normal((k,) + x.shape) * s[None]
        for j in range(M.m):
            miss = np.isnan(x[:, j])
            if miss.any(): d[:, miss, j] = rng.choice(x[~miss, j], size=(k, miss.sum()))
        out.append(np.einsum("nck,nk->nc", M.phi(d.reshape(-1, M.m)).reshape(k, nC, M.n), thetas[a:a + k]))
    return np.vstack(out)
th=MP.sample_theta(10000,rng); r=ranks(noisy_U(MP,th)); mr=r.mean(0); o=np.argsort(mr)
OUT={"neighbours":[], "removals":{}}
for a,b in zip(o[:-1],o[1:]):
    d=r[:,b]-r[:,a]; se=d.std()/100; print(f"{C[a]:15s}{mr[a]:6.2f} | {C[b]:15s}{mr[b]:6.2f} gap {mr[b]-mr[a]:.3f} se {se:.3f} z {(mr[b]-mr[a])/se:.1f}")
    OUT["neighbours"].append({"upper":C[a],"lower":C[b],"gap":round(float(mr[b]-mr[a]),3),"se":round(float(se),3)})
# leave graduation / advanced courses out under Theta_S (point data), top3
r7=np.random.default_rng(7); th4=MP.sample_theta(4000,r7); PH=MP.phi(fill_missing(X[MP.inds]).values)
for ind in ("E2r_grad_district","E1_adv_course"):
    j=MP.inds.index(ind); d=MP.dom[j]; same=[k for k in range(MP.m) if MP.dom[k]==d and k!=j]
    t=th4.copy(); dt=t.reshape(len(t),MP.m,3); tot=dt[:,[k for k in range(MP.m) if MP.dom[k]==d]].sum((1,2))
    dt[:,j]=0; rest=dt[:,same].sum((1,2)); dt[:,same]*=(tot/rest)[:,None,None]
    rr=ranks(dt.reshape(len(t),-1)@PH.T); p=(rr==1).mean(0); oo=np.argsort(-p)[:3]
    print(ind, "; ".join(f"{C[i]} {p[i]:.3f}" for i in oo)); OUT["removals"][ind]={C[i]:round(float(p[i]),3) for i in oo}
json.dump(OUT,open(RES/"table1_precision.json","w"),indent=1)
