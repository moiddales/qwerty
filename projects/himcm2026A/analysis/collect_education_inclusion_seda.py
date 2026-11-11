"""Select SEDA background for local noncommercial research only; exclude from Git."""
import csv,json,collections,re
from collect_education_inclusion import BASE,RAW,META
OUT=BASE/'data/extracted/education_inclusion'
leas=set(json.loads((META/'related_lea_ids.json').read_text()))
for file in OUT.glob('crdc_*_high_school_city_crosswalk.csv'):
 with file.open() as f:
  for r in csv.DictReader(f):leas.add(r['leaid'])
selected=RAW/'seda_selected_related_districts_2025.2_LOCAL_ONLY.csv';count=0;groups=set();years=set()
with (RAW/'seda_admindist_annual_gcs_2025.2.csv').open() as src,selected.open('w',newline='') as dst:
 reader=csv.DictReader(src);w=csv.DictWriter(dst,reader.fieldnames);w.writeheader()
 for r in reader:
  if r['sedaadmin'].zfill(7) in leas:w.writerow(r);count+=1;groups.add(r['sedaadmin']);years.add(r['year'])
info=dict(selected_rows=count,selected_districts=len(groups),years=sorted(years),selection='NCES or CRDC LEAs associated with high-school-offering school points in 25 Census places; district measures cover whole districts; elementary/middle school grades 3-8 background',raw_file=str(selected.relative_to(BASE)),publication_status='LOCAL ONLY: no redistribution right established; exclude SEDA raw and selected data from Git',citation='Reardon et al. (2026), Stanford Education Data Archive (Version SEDA 2025.2), https://doi.org/10.25740/np279jm6134')
(META/'seda_local_selection.json').write_text(json.dumps(info,indent=2));print(json.dumps(info))
