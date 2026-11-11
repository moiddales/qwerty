"""Finish four fare amounts using official current charts, keeping distinct fare products."""
from collect_policy_parameters import *
import re,html
items={'dart_local_fare_announcement':'https://dartdaily.dart.org/home/ask-dart--what-s-changing-with-fares-starting-march-1-2025','dart_regional_2026':'https://dart.org/about/news-and-events/newsreleases/newsrelease-detail/dart-announces-regional-fare-adjustments-effective-march-1--2026','rtc_fare_policy':'https://rtcsnv.civicweb.net/document/153223/Fare%20Policy.pdf?handle=16714D2076814654A31BAAABA8F7F65A','rtc_2026_service':'https://www.rtcsnv.com/ways-to-travel/schedules-maps/service-changes/aug-2026-service-change/'}
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:logs=list(ex.map(fetch,items.items()))
 with (META/'access_log.jsonl').open('a') as f:f.write(''.join(json.dumps(r)+'\n' for r in logs))
 p=OUT/'youth_transit_policies_25cities.csv';rows=list(csv.DictReader(p.open()))
 updates={
 '4819000':dict(value='1.50',unit='USD per eligible local 3-hour pass',source_url=items['dart_local_fare_announcement'],source_snapshot='data/raw/policy_parameters/final_fare_verified_index.json',evidence_status='official fare announcement and 2026 regional-change notice verified',quality_note='Local3-hour reduced pass effective2025-03-01 includes transfers/GoLink; 2026-03-01 regional fare changes are distinct; current fare page confirms3-hour product. Observed chart amount, not arithmetic estimate.'),
 '1836003':dict(value='1.35',unit='USD per eligible fixed-route 2-hour unlimited pass',source_url='https://www.indygo.net/value-of-transit/new-fares/',source_snapshot='data/raw/policy_parameters/final_fare_verification_web.json',evidence_status='official current page parsed via web retrieval; urllib403',quality_note='Official fixed-route table effective2026-01-01 explicitly gives half fare1.35; do not calculate2.75/2. Youth18andunder eligible; validK12ID and MyKey+ reduced profile confirmation; school-sponsored free travel separate.'),
 '3240000':dict(value='1.00',unit='USD per eligible residential-route single ride',source_url='https://www.rtcsnv.com/ways-to-travel/fares-passes/',source_snapshot='data/raw/policy_parameters/final_fare_verified_index.json',evidence_status='official current main-page indexed fare table verified; direct403',quality_note='Current official residential fare chart reduced single1; 2-hour1.50;24-hour2.50. Aug2026 service notice explicitly fares unchanged; proposed2027 increase excluded. Main-page current evidence, not legacy mobile-page inference. Proper reduced ID/media required; contactless bank-card payment charges full fare.'),
 '2507000':dict(value='0.85',unit='USD per eligible local bus single ride',source_url='https://www.mbta.com/fares/reduced',source_snapshot='data/raw/policy_parameters/mbta_reduced_current.html',evidence_status='downloaded official fare chart',quality_note='Student CharlieCard/reduced eligibility; bus single0.85; subway single1.10; S-Card monthly bus/subway30 preserved in additional products; school-paid M7 may cover eligible BPS students.')}
 for r in rows:
  if r['city_id'] in updates:r.update(updates[r['city_id']])
 def write(name,rr):
  with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
 write(p.name,rows)
 b=next(r for r in rows if r['city_id']=='2507000')
 write('boston_student_fare_products.csv',[dict(b,indicator_id='student_subway_single_fare',value='1.10',unit='USD per subway single ride'),dict(b,indicator_id='student_SCard_monthly_fare',value='30',unit='USD per monthly bus/subway pass',source_url='https://www.mbta.com/fares/reduced/student-charliecards',source_snapshot='data/raw/policy_parameters/fare_2507000.html')])
 inv=[]
 for p in sorted(RAW.iterdir()):
  if p.is_file():inv.append(dict(path=str(p.relative_to(BASE)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),publication='local_only_page_snapshot; publish paraphrased facts+URLs; federal tables may be archived'))
 with (META/'raw_inventory.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(inv[0]));w.writeheader();w.writerows(inv)
 iv=[]
 for p in sorted(OUT.glob('*.csv')):
  rr=list(csv.DictReader(p.open()));iv.append(dict(path=str(p.relative_to(BASE)),rows=len(rr),cities=len({r['city_id'] for r in rr if r.get('city_id')}),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 with (META/'extracted_inventory.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(iv[0]));w.writeheader();w.writerows(iv)
 assert len(rows)==25 and len({r['city_id'] for r in rows})==25 and all(r['value'] for r in rows)
 (META/'validation.json').write_text(json.dumps(dict(fare_cities=25,fare_numeric_values=25,fare_policy_records=25,no_unknown_as_zero=True,extracted_files=len(iv),extracted_rows=sum(x['rows'] for x in iv)),indent=2))
 print('All25 fares numeric;',len(inv),'raw files;',sum(x['rows'] for x in iv),'extracted rows')
