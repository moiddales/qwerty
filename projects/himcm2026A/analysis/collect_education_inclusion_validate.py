"""Validate geography coverage, suppression handling and publishable artifact inventory."""
import csv,json,pathlib,hashlib,zipfile,collections,gzip
from collect_education_inclusion import BASE,RAW,META
OUT=BASE/'data/extracted/education_inclusion'
cities={r['city_id'] for r in csv.DictReader((BASE/'data/metadata/cities.csv').open())}
checks={};inventory=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
for p in sorted(OUT.rglob('*')):
 if not p.is_file():continue
 nrows='';ncity=''
 if p.suffix=='.csv':
  with p.open() as f:
   reader=csv.DictReader(f);nrows=0;ids=set()
   for r in reader:
    nrows+=1
    if 'city_id' in r:
     assert r['city_id'] in cities,(p,r['city_id']);ids.add(r['city_id'])
   ncity=len(ids)
 inventory.append(dict(path=str(p.relative_to(BASE)),bytes=p.stat().st_size,sha256=sha(p),data_rows=nrows,cities=ncity,git_action='use .csv.gz copy; omit this large csv' if p.stat().st_size>50*1024*1024 else 'include with source attribution'))
for name in ['education_city_indicators.csv','ccd_2425_city_indicators.csv','ccd_2425_grade_enrollment_city_indicators.csv']:
 rs=list(csv.DictReader((OUT/name).open()));assert {r['city_id'] for r in rs}==cities;checks[name]=dict(rows=len(rs),cities=25)
rs=list(csv.DictReader((OUT/'education_core_school_indicators.csv').open()));assert all(not r['value'].startswith('-') for r in rs);assert all(r['value']=='' for r in rs if r['raw_value'].startswith('-'));checks['CRDC_negative_codes_excluded']=True
r=list(csv.DictReader((META/'crdc_city_coverage.csv').open()));assert len(r)==50 and all(int(x['matched_high_schools'])>0 for x in r)
checks['CRDC_all_25_each_year']=True
r=list(csv.DictReader((OUT/'hrc_2025_city_policy_indicators.csv').open()));assert len({x['city_id'] for x in r if x['value']!=''})==24 and all(0<=float(x['value'])<=100 for x in r if x['value']);checks['HRC_24_plus_missing_DC']=True
r=list(csv.DictReader((OUT/'local_graduation_supplement_indicators.csv').open()));assert {'1714000','5363000'}<={x['city_id'] for x in r if x['value']!=''};checks['Chicago_Seattle_official_supplements']=True
# Track all archive structures without duplicating national data in Git.
members=[]
for p in sorted(RAW.glob('*.zip')):
 with zipfile.ZipFile(p) as z:
  for info in z.infolist():members.append(dict(archive=p.name,member=info.filename,uncompressed_bytes=info.file_size,compressed_bytes=info.compress_size,crc32=hex(info.CRC),compression_method=info.compress_type))
for name,rows in [('extracted_inventory.csv',inventory),('archive_members.csv',members)]:
 with (META/name).open('w',newline='') as f:w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
# Raw publication decisions are explicit and separate from whether downloads succeeded.
raw_inventory=[]
for p in sorted(RAW.iterdir()):
 if not p.is_file():continue
 reason='include, public data or source-access evidence'
 if p.name.lower().startswith('seda'):reason='LOCAL ONLY: redistribution permission not established'
 elif p.name.startswith('hrc_'):reason='LOCAL ONLY: copyrighted original; use extracted numeric facts'
 elif p.name=='cps_graduation_page.html':reason='LOCAL ONLY: original webpage; use extracted numeric facts'
 elif p.stat().st_size>50*1024*1024:reason='LOCAL NATIONAL PACKAGE: archive metadata and selected subset; root decides external release storage'
 elif p.stat().st_size==0:reason='EMPTY RESPONSE: access evidence only, not data'
 raw_inventory.append(dict(path=str(p.relative_to(BASE)),bytes=p.stat().st_size,sha256=sha(p),publication=reason))
with (META/'raw_publication_inventory.csv').open('w',newline='') as f:w=csv.DictWriter(f,raw_inventory[0].keys());w.writeheader();w.writerows(raw_inventory)
poly=BASE/'data/raw/mobility_opportunities/census_acs2025_city_polygons.json'
(META/'dependencies.json').write_text(json.dumps([dict(path=str(poly.relative_to(BASE)),sha256=sha(poly),note='Official ACS2025 Census place polygons, ESRI rings, EPSG4326; supplied by mobility collector')],indent=2))
(META/'validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
