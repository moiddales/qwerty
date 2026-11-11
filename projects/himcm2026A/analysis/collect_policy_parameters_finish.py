from collect_policy_parameters import *
import re,html
more={'boston_m7':'https://www.bostonpublicschools.org/bps-departments/transportation/students-families/mbta-passes','rtc_reduced':'https://www.rtcsnv.com/ways-to-travel/fares-passes/reduced-fare/','rtc_mobile':'https://rtcws.rtcsnv.com/mobile/geoFares.html','indy_fares':'https://www.indygo.net/fares-and-passes/','cdc_connectedness_2021':'https://www.cdc.gov/mmwr/volumes/72/su/su7201a2.htm','cdc_connectedness_2023':'https://www.cdc.gov/mmwr/volumes/73/su/su7304a9.htm','nhts_trends':'https://nhts.ornl.gov/media/2022/pub/2022_NHTS_Summary_Travel_Trends.pdf'}
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:logs=list(ex.map(fetch,more.items()))
with (META/'access_log.jsonl').open('a') as f:f.write(''.join(json.dumps(r)+'\n' for r in logs))
def write(name,rows):
 with (OUT/name).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
rows=list(csv.DictReader((OUT/'youth_transit_policies_25cities.csv').open()))
updates={'0668000':('1.25','Local single ride; 2-hour Clipper transfers; youth5–18'),'3712000':('1.10','Local bus/rail K12 seven days; valid Transit or Student ID; modernization page future tense kept separate'),'4824000':('1.00','Children6–18; students over18 need valid student ID; local single ride'),'4260000':('0','School-determined eligible card; up to8 trips/schoolday5:30am–8pm; not universal leisure access')}
for r in rows:
 if r['city_id'] in updates:r['value'],r['quality_note']=updates[r['city_id']];r['unit']='USD per eligible local ride'
 if r['city_id']=='3712000':r.update(source_url=EXTRA['charlotte_fares'],source_snapshot='data/raw/policy_parameters/charlotte_fares.html',eligibility='K12 valid Transit or Student ID; children12andunder accompanied')
 if r['city_id']=='2507000':r['quality_note']='Official MBTA page downloaded successfully: Student S-Card $30 monthly or $10 seven-day; school-paid M7 differs; BPS eligible grades7–12 also summer use';r['value']='30';r['unit']='USD per S-Card monthly bus/subway pass'
 if r['city_id']=='1836003':r['evidence_status']='official page parsed via web retrieval; urllib403';r['source_snapshot']='data/raw/policy_parameters/official_parsed_fare_fallback.json'
 if r['city_id']=='3240000':r['evidence_status']='official current index eligibility plus downloaded official mobile fare page; mobile undated';r['source_snapshot']='data/raw/policy_parameters/rtc_mobile.html';r['quality_note']='Reduced youth fare verified; official mobile lists residential single$1 but undated legacy page (SDX label); current numeric fare not asserted. Eligibility current main-page indexed evidence in search_evidence_06.json.'
write('youth_transit_policies_25cities.csv',rows)
base=dict(city_id='1150000',city_name='Washington',state='District of Columbia',source_id='S28',observation_period='policy page accessed2026-11-11; guidance June2015 where indicated',geography_type='DC Public Schools; not all private/charter schools',source_geo_id='DCPS',unit='documented policy fact')
facts=[('dcps_bullying_gender_identity_protection','DCPS bullying definition explicitly includes actual/perceived sexual orientation and gender identity/expression',EXTRA['dc_bullying'],'Policy existence does not measure implementation or student experience; no MEI score'),('dcps_care_grievance_support','CARE receives discrimination and protected-class bullying complaints and works with school staff on resolution',EXTRA['dc_grievance'],'Administrative support process; no outcome score'),('dcps_transgender_guidance','June2015 guidance addresses gender identity/expression discrimination and gender-specific facilities',EXTRA['dc_gender_guidance'],'Historical official guidance still linked from current grievance page; not asserted independently current law')]
write('dc_inclusion_policy_facts.csv',[dict(**base,indicator_id=i,value=v,source_url=u,quality_note=q) for i,v,u,q in facts])
res=[('3651000','NYC DOE high-school admissions',EXTRA['nyc_admissions'],'entry_only; program-specific eligibility and priorities require separate extraction'),('1714000','CPS GoCPS',EXTRA['cps_admissions'],'entry_only; applications/selection not equivalent to school physical location'),('1150000','DCPS residency',EXTRA['dc_residency'],'entry_only; eligibility proof not yet extracted')]
write('admissions_reserve.csv',[dict(city_id=c,source_id='S28',topic=t,source_url=u,status=s,accessed='2026-11-11') for c,t,u,s in res])
surveys=[('YRBS2021_connectedness','2021','US high school students','National weighted school survey; examines perceived school connectedness and associations with risk experiences; cross-sectional, no causal threshold',more['cdc_connectedness_2021'],EXTRA['cdc_yrbs_data'],'published tables downloaded; no city estimates'),('YRBS2023_protective_factors','2023','US high school students','School connectedness associated with lower prevalence of mental-health/suicide-risk indicators; adjusted prevalence ratio0.63–0.70 in article',more['cdc_connectedness_2023'],EXTRA['cdc_yrbs_data'],'published tables downloaded; associations not causal scoring weights'),('NHTS2022','2022','US household travel; age-specific analyses possible','Travel diary and household/person/trip records; survey weights and sample design required',EXTRA['nhts_data'],EXTRA['nhts_methods'],'download and method pages plus travel-trends report; microdata not acquired in this task'),('CDC_School_Health_Profiles','2022;2024','secondary schools; participating states/large urban school districts','Principal and lead health-education-teacher surveys about school policies/practices',EXTRA['profiles_methods'],EXTRA['profiles_methods'],'actual national CSV and selected10of25 districts already in education_inclusion; not student belonging outcome')]
write('survey_parameter_reserve.csv',[dict(source_id='S29',survey=i,observation_period=y,geography=g,fact=f,source_url=u,method_url=m,quality_note=q) for i,y,g,f,u,m,q in surveys])
# Preserve DOL table exactly as textual cells, including footnote markers; no city/minor applicability inferred.
class TableParser(__import__('html.parser',fromlist=['HTMLParser']).HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.row=None;self.cell=None
 def handle_starttag(self,t,a):
  if t=='tr':self.row=[]
  if t in ('td','th'):self.cell=[]
 def handle_data(self,s):
  if self.cell is not None:self.cell.append(s)
 def handle_endtag(self,t):
  if t in ('td','th') and self.cell is not None:
   if self.row is not None:self.row.append(' '.join(' '.join(self.cell).split()))
   self.cell=None
  if t=='tr' and self.row is not None:
   if self.row:self.rows.append(self.row)
   self.row=None
for n in ['dol_consolidated_minimum_wages','cdc_connectedness_2021','cdc_connectedness_2023']:
 p=RAW/(n+'.html')
 if not p.exists():continue
 a=TableParser();a.feed(p.read_text());write(n+'_tables.csv',[dict(table_row=j,raw_cells_json=json.dumps(row),source_url=EXTRA.get(n,more.get(n)),quality_note='Verbatim table cells; notes and definitions in archived official page; not a city score') for j,row in enumerate(a.rows)])
# Hash inventory and archive instructions for all snapshots.
inv=[]
for p in sorted(RAW.iterdir()):
 if p.is_file():inv.append(dict(path=str(p.relative_to(BASE)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),publication='local_only_page_snapshot; publish paraphrased facts+URLs; federal tables may be archived'))
with (META/'raw_inventory.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(inv[0]));w.writeheader();w.writerows(inv)
print('Completed',len(rows),'cities;',len(inv),'raw files')
