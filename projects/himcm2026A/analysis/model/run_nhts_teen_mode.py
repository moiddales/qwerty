"""National travel of 14-18-year-olds, NHTS 2022 V2.1 (weighted point estimates; no design-based SE).

    cd projects/himcm2026A/analysis/model && python run_nhts_teen_mode.py
"""
import json
import pandas as pd
from core import RES

N = RES.parent / "supplement_20261111/nhts"
t = pd.read_csv(N / "trips_age14_18.csv.gz")
p = pd.read_csv(N / "persons_age14_18.csv.gz")
w = t.WTTRDFIN
out = {"trips_n": len(t),
       "trip_share_private_vehicle_passenger": round(float((w * (t.PSGR_FLG == 1)).sum() / w.sum()), 3),
       "trip_share_private_vehicle_driver": round(float((w * (t.DRVR_FLG == 1)).sum() / w.sum()), 3),
       "trip_share_other_modes": round(float((w * (t.PSGR_FLG == -1)).sum() / w.sum()), 3)}
for lo, hi in ((14, 15), (16, 17), (18, 18)):
    q = p[(p.R_AGE >= lo) & (p.R_AGE <= hi)]
    out[f"driver_share_age{lo}_{hi}"] = round(float((q.WTPERFIN * (q.DRIVER == 1)).sum() / q.WTPERFIN.sum()), 3)
    out[f"persons_age{lo}_{hi}"] = len(q)
json.dump(out, open(RES / "nhts_teen_mode.json", "w"), indent=1)
print(json.dumps(out, indent=1))
