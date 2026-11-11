"""Official policy snapshots and explicitly scoped manual fact extraction; no legal eligibility inference."""
import csv,json,hashlib,urllib.request,urllib.error,datetime,concurrent.futures
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];RAW=BASE/'data/raw/policy_parameters';OUT=BASE/'data/extracted/policy_parameters';META=BASE/'data/metadata/policy_parameters'
for p in (RAW,OUT,META):p.mkdir(exist_ok=True,parents=True)
DATA=[
('3651000','MTA/NYC DOE','0','eligible school-issued Student OMNY; four trips daily year-round','school eligibility; not universal age entitlement','https://www.schools.nyc.gov/school-life/transportation/student-omny-cards'),
('0644000','LA Metro','0','GoPass at participating K12/adult/community colleges','participating school required; other K12 reduced fare separate','https://www.metro.net/fares/student-gopass/'),
('1714000','CTA','0.75','full-time elementary/high school students age 7–20; Student Ventra','24/7 year-round 2026 pilot; fare per ride with transfers','https://www.transitchicago.com/students/'),
('4835000','Houston METRO','0.60','K12/college student discounted fare card; enrollment evidence','local bus/rail; park-and-ride variable','https://www.ridemetro.org/fares/all-about-fares'),
('0455000','Valley Metro','1','youth age 6–18; proof of age/reduced fare media','local single ride; Tempe free program not applied to Phoenix','https://www.valleymetro.org/fares'),
('4260000','SEPTA','','school-determined eligible Student Fare Card; generally grades 7–12 at least 1.5 miles away','free eligible card; up to 8 school-day trips 5:30am–8pm; not universal leisure access','https://wwww.septa.org/fares/student-fare-card-program/'),
('4865000','VIA','0','active students age 12–18 at Bexar County public/private/charter/home schools','Fall2026/Spring2027 semester passes require registration','https://www.viainfo.net/student-passes/'),
('0666000','MTS/NCTD','0','age 18 and under; verified Youth PRONTO','Youth Opportunity Pass pilot through 2027-06-30; fixed route scope','https://www.sdmts.com/fares/youth-opportunity-pass-program'),
('4819000','DART','','qualifying youth and high-school students; proof required','50% reduced fare program; no unverified local numeric fare assigned','https://www.dart.org/fare/general-fares-and-overview/reduced-fares/'),
('4827000','Trinity Metro','1','youth age 5–19 with ID','local single ride; FWISD grades9–12 separately free in2026–27','https://ridetrinitymetro.org/tickets/'),
('1235000','JTA','0','Duval County middle/high-school students with school ID or Purple STAR','fixed bus and First Coast Flyer; seven days year-round','https://www.jtafla.com/rider-guide/fares-passes'),
('4805000','CapMetro','0','18 and under; student ID or CapMetro student ID','detailed eligibility page says18andunder; generic page has under18 wording','https://www.capmetro.org/rfid'),
('0668000','VTA','','youth age5–18 qualify for discounted fares','discount verified; amount retained blank pending fare-table extraction','https://www.vta.org/go/fares'),
('3712000','CATS','','student grades6–12; Transit ID with enrollment evidence','fare reform proposes age6–19; do not assume proposed rule effective','https://www.charlottenc.gov/CATS/Fares-Passes/Transit-IDs'),
('3918000','COTA','1','children age5–12; school educational-pass agreements separately','older teens not universally eligible for child fare; local single ride','https://cota.com/contact/faq/'),
('1836003','IndyGo','','youth age6–18 with valid K12 student ID','half standard fare; participating schools may sponsor free travel','https://www.indygo.net/mykeyplus/ride-with-mykey/'),
('0667000','SFMTA Muni','0','18 and under','regular Muni; cable cars excluded','https://www.sfmta.com/getting-around/muni/fares'),
('5363000','King County Metro','0','age0–18','Youth ORCA encouraged; regional partner operators have own conditions','https://kingcounty.gov/en/dept/metro/fares-and-payment/prices'),
('0820000','RTD','0','19 and under; proof of eligibility','Zero Fare for Youth permanent program all RTD services','https://www.rtd-denver.com/zero-fare-for-youth'),
('4752006','WeGo','1','19 and younger','local bus fare; Star commuter rail origin-dependent','https://www.wegotransit.com/faq/'),
('4055000','EMBARK','0','18 and younger within service area; Haul Pass application','fixed route buses/RAPID NW/OKC Streetcar','https://www.embarkok.com/bus/haul-pass'),
('1150000','WMATA/DDOT','0','DC resident age5–21 enrolled DC elementary/secondary public/charter/private/parochial school, or qualifying DC ward','Kids Ride Free card; school-related travel within DC; not all youth visitors','https://ddot.dc.gov/page/kids-ride-free-frequently-asked-questions'),
('4824000','Sun Metro','','children6–18/student eligibility; proof may be requested','reduced fare verified; numeric amount pending table extraction','https://sunmetro.net/fares/fares-and-passes'),
('3240000','RTC Southern Nevada','','youth6–17 or K12 students; qualifying ID','reduced fare verified; distinguish residential/Strip pass products','https://www.rtcsnv.com/ways-to-travel/fares-passes/'),
('2507000','MBTA','','middle/high-school Student CharlieCard program','school-paid M7 vs user-loaded S-Card; direct official snapshot attempted; no proxy mirror evidence accepted','https://www.mbta.com/fares/reduced/student-charliecards')]
EXTRA={
'charlotte_fares':'https://www.charlottenc.gov/CATS/Fares-Passes',
'charlotte_modernization':'https://www.charlottenc.gov/CATS/Fares-Passes/Fare-Modernization-Program',
'vta_eligibility':'https://www.vta.org/faq/what-are-age-limits-discounted-fares',
'indygofares':'https://www.indygo.net/mykeyplus/ride-with-mykey/',
'dc_bullying':'https://dcps.dc.gov/bullying',
'dc_grievance':'https://dcps.dc.gov/page/studentparentvisitor-grievance-process',
'dc_gender_guidance':'https://dcps.dc.gov/sites/default/files/dc/sites/dcps/publication/attachments/DCPS%20Transgender%20Gender%20Non%20Conforming%20Policy%20Guidance.pdf',
'dol_state_minimum_wages':'https://www.dol.gov/agencies/whd/minimum-wage/state',
'dol_consolidated_minimum_wages':'https://www.dol.gov/agencies/whd/mw-consolidated',
'cps_admissions':'https://www.cps.edu/gocps/',
'nyc_admissions':'https://www.schools.nyc.gov/enrollment/enroll-grade-by-grade/high-school',
'dc_residency':'https://enrolldcps.dc.gov/node/71',
'cdc_connectedness':'https://www.cdc.gov/mmwr/volumes/73/su/su7304a2.htm',
'cdc_yrbs_data':'https://www.cdc.gov/yrbs/data/index.html',
'nhts_data':'https://nhts.ornl.gov/downloads',
'nhts_methods':'https://nhts.ornl.gov/documentation',
'profiles_methods':'https://www.cdc.gov/school-health-profiles/about/index.html'}
def fetch(item):
 name,url=item;p=RAW/(name+('.pdf' if '.pdf' in url else '.html'));r=dict(source_id='S28' if not name.startswith(('cdc','nhts','profiles')) else 'S29',url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),local_path=str(p.relative_to(BASE)),license='Official public web page; factual extraction; original content redistribution not established')
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=55) as f:b=f.read();r.update(http_status=f.status,content_type=f.headers.get('Content-Type'),final_url=f.url)
  p.write_bytes(b);r.update(status='downloaded' if b else 'empty_response',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except Exception as e:r.update(status='failed',reason=str(e))
 return r
if __name__=='__main__':
 items=[('fare_'+r[0],r[-1]) for r in DATA]+list(EXTRA.items())
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:logs=list(ex.map(fetch,items))
 (META/'access_log.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in logs))
 cities={r['city_id']:r for r in csv.DictReader((BASE/'data/metadata/cities.csv').open())};rows=[]
 for cid,agency,value,elig,note,url in DATA:
  log=next(r for r in logs if r['url']==url)
  rows.append(dict(city_id=cid,city_name=cities[cid]['city_name'],state=cities[cid]['state'],source_id='S28',indicator_id='youth_student_fare_policy',value=value,unit='USD per eligible local ride' if value else 'policy fact; numeric fare not extracted',observation_period='accessed 2026-11-11; policy effective dates in note',geography_type='selected primary transit operator; not complete city operator inventory',source_geo_id=agency,source_url=url,quality_note=note,eligibility=elig,evidence_status=log['status'],source_snapshot=log.get('local_path','')))
 with (OUT/'youth_transit_policies_25cities.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print(json.dumps({'attempts':len(logs),'downloaded':sum(r['status']=='downloaded' for r in logs),'fare_city_rows':len(rows),'failed':[r for r in logs if r['status']!='downloaded']},indent=2))
