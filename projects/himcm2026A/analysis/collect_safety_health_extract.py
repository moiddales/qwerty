"""Normalize downloaded data without conflating geographic or age scopes."""
from collect_safety_health import *
import io,re,collections,openpyxl
cities=list(csv.DictReader((BASE/'data/metadata/cities.csv').open()))
cc=list(csv.DictReader((BASE/'data/metadata/city_county_crosswalk.csv').open()))
byid={c['city_id']:c for c in cities}
fields=['city_id','city_name','state','source_id','indicator_id','value','unit','observation_period','geography_type','source_geo_id','source_url','quality_note']
out=[]; coverage=[]
def write(name,rows,fs=None):
 if not fs:fs=list(dict.fromkeys(k for r in rows for k in r))
 with (EXT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(rows)
def add(c,s,i,v,u,year,g,gid,url,note,**extra):
 out.append(dict(zip(fields,[c['city_id'],c['city_name'],c['state'],s,i,'' if v is None else v,u,year,g,gid,url,note]),**extra))
def cname(c):
 return c['city_name'].replace(' city (balance)','').replace(' city','').replace('Nashville-Davidson metropolitan government (balance)','Nashville')
def norm(s):return re.sub('[^a-z]','',str(s).lower())
# Current official agency registry maps names to ORIs; it does not establish historical boundary identity.
agency_map={};agency_rows=[]
for c in cities:
 d=json.loads((RAW/f"fbi_agencies_{c['state_abbr']}.json").read_text())
 names={r['agency_name']:r for a in d.values() for r in a}
 name=cname(c)+' Police Department'
 overrides={'3651000':'New York City Police Department','1235000':"Jacksonville Sheriff's Office",'3712000':'Charlotte-Mecklenburg Police Department','4752006':'Metropolitan Nashville Police Department','3240000':'Las Vegas Metropolitan Police Department'}
 name=overrides.get(c['city_id'],name)
 r=names[name];agency_map[c['city_id']]=r['ori'];agency_rows.append(dict(city_id=c['city_id'],**r,mapping_note='Associated primary agency; current registry; does not verify historical Census-place boundary equality'))
write('fbi_city_agency_registry_crosswalk.csv',agency_rows)
# FBI Table 8 population is the agency population used in that source.
fbiwide=[]
for y in range(2021,2026):
 w=openpyxl.load_workbook(EXT/f'fbi_table8_{y}.xlsx',read_only=True,data_only=True)
 rows=list(w.active.values);st='';lookup={};notes=[r[0] for r in rows[4:] if r[0] and not r[1]]
 for r in rows[4:]:
  if not r[1]:continue
  if r[0]:st=re.sub(r'\d+$','',r[0]).strip()
  lookup[(norm(st),norm(r[1]))]=r
 for c in cities:
  names=[cname(c)]
  if c['city_id']=='1836003':names=['Indianapolis','Indianapolis Metropolitan']
  if c['city_id']=='4752006':names=['Metropolitan Nashville Police Department']
  if c['city_id']=='3712000':names=['Charlotte-Mecklenburg']
  if c['city_id']=='3240000':names=['Las Vegas Metropolitan Police Department']
  r=next((lookup[(norm(c['state']),norm(n))] for n in names if (norm(c['state']),norm(n)) in lookup),None)
  coverage.append(dict(city_id=c['city_id'],source_id='S08',year=y,status='available' if r else 'not_in_table8',note='12 complete months required by Table 8 methodology; agency boundary not verified as Census balance'))
  if r:
   note='Table 8 requires 12 complete months; police agency geography; FBI agency population retained; Charlotte-Mecklenburg, Las Vegas Metropolitan, Nashville Metropolitan are associated agency proxies and are not Census city boundaries; '+ ' | '.join(notes)
   if re.search(r'\d',str(r[1])):note+=' Agency name footnote: '+str(r[1])
   fbiwide.append(dict(city_id=c['city_id'],year=y,source_state=c['state'],source_city=r[1],ori=agency_map[c['city_id']],agency_population=r[2],reporting_months=12,violent_crime=r[3],murder=r[4],rape=r[5],robbery=r[6],aggravated_assault=r[7],notes=note))
   for i,v in zip(['agency_population','violent_crime','murder','rape','robbery','aggravated_assault'],r[2:8]):
    add(c,'S08',i,v,'persons' if i=='agency_population' else 'reported offenses',y,'police agency',agency_map[c['city_id']],'https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads',note,reporting_months=12)
write('fbi_city_wide.csv',fbiwide)
# PLACES adult background and both confidence interval types, all source fields preserved.
places=list(csv.DictReader((RAW/'places_2025.csv').open()));pmap={r['PlaceFIPS'].zfill(7):r for r in places};ps=[]
for c in cities:
 r=pmap.get(c['city_id']);coverage.append(dict(city_id=c['city_id'],source_id='S15',year='2025 release',status='available' if r else 'unmatched',note='Adult model estimates only'))
 if r:
  ps.append(r)
  for k,v in r.items():
   if k.endswith('Prev'):
    ci=r.get(k.replace('Prev','95CI'),'')
    add(c,'S15',k,v,'percent','2025 release; BRFSS observation year varies by measure','Census place',c['city_id'],'https://data.cdc.gov/d/vgc8-iyc4','Adult model estimate; not adolescent outcome; empty stays missing',confidence_interval=ci)
write('places_25city_wide.csv',ps)
# SAMHSA postal city match; retain facility rows and exact age acceptance, no claim of boundary geocoding.
w=openpyxl.load_workbook(RAW/'samhsa_mh_facilities_2025.xlsx',read_only=True,data_only=True)
it=iter(w['Facilities List'].values);head=next(it);fac=[dict(zip(head,r)) for r in it];matched=[]
write('samhsa_service_code_reference.csv',[dict(zip(['category_code','category','service_code','label','description'],r)) for r in list(w['Service Code Reference'].values)[1:]])
for c in cities:
 names=[cname(c)]
 if c['city_id']=='3651000':names=['New York','New York City','Brooklyn','Bronx','Queens','Staten Island']
 rows=[r for r in fac if norm(r['city']) in [norm(n) for n in names] and r['state']==c['state_abbr']]
 for r in rows:matched.append(dict(city_id=c['city_id'],**r))
 youth=[r for r in rows if 'CH/AD' in str(r['service_code_info']).split()]
 note='Facility postal-city name match, not point-in-Census-boundary; CH/AD accepts age 17 or younger; no capacity or availability measure; NYC nonstandard Queens postal names may be missed'
 add(c,'S14','listed_mh_facilities_children_adolescents',len(youth),'listed facilities','2025 directory (2024 N-SUMHSS)','facility postal city',','.join(names),'https://www.samhsa.gov/data/report/2025-national-directory-mental-health-treatment-facilit',note)
 coverage.append(dict(city_id=c['city_id'],source_id='S14',year=2025,status='postal_city_proxy',note=note))
write('samhsa_city_facilities.csv',matched)
# EPA county tables have names, not FIPS. Match against county names from monitor file FIPS crosswalk.
with zipfile.ZipFile(RAW/'annual_conc_by_monitor_2025.zip') as z:
 mons=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8-sig')))
countynames={(r['State Name'],r['County Name']):r['State Code']+r['County Code'] for r in mons}
monout=[]
for r in mons:
 county=r['State Code']+r['County Code']
 for m in cc:
  if county==m['county_id']:monout.append(dict(city_id=m['city_id'],county_id=county,**r))
write('epa_monitor_2025_city_counties.csv',monout)
for y in range(2021,2026):
 with zipfile.ZipFile(RAW/f'annual_aqi_by_county_{y}.zip') as z:
  rows=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8-sig')))
 for r in rows:
  gid=countynames.get((r['State'],r['County']))
  for m in cc:
   if gid!=m['county_id']:continue
   c=byid[m['city_id']]
   for k,v in r.items():
    if k not in ['State','County','Year']:
     add(c,'S10','aqi_'+re.sub(r'[^a-z0-9]+','_',k.lower()),v,'days' if 'Days' in k else 'AQI',y,'county',gid,f'https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_county_{y}.zip','County ambient monitor background; multiple counties retained separately; not city-specific',city_population_share=m[f'city_population_share_{y}'])
# CBSA AQI background, preserving shared metropolitan values across different cities.
cbsa=list(csv.DictReader((BASE/'data/metadata/city_county_cbsa_crosswalk.csv').open()))
for y in range(2021,2026):
 with zipfile.ZipFile(RAW/f'annual_aqi_by_cbsa_{y}.zip') as z:
  rows=list(csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding='utf-8-sig')))
 for c in cities:
  ids={m['cbsa_id'] for m in cbsa if m['city_id']==c['city_id']}
  for r in rows:
   if r['CBSA Code'] not in ids:continue
   for k,v in r.items():
    if k not in ['CBSA','CBSA Code','CBSA Name','Year']:
     add(c,'S10','cbsa_aqi_'+re.sub(r'[^a-z0-9]+','_',k.lower()),v,'days' if 'Days' in k else 'AQI',y,'CBSA',r['CBSA Code'],f'https://aqs.epa.gov/aqsweb/airdata/annual_aqi_by_cbsa_{y}.zip','Regional ambient monitor background; shared CBSA values are not city-specific; city share describes residents in CBSA, not monitor coverage',cbsa_city_population_share=sum(float(m[f'city_population_share_{y}']) for m in cbsa if m['city_id']==c['city_id'] and m['cbsa_id']==r['CBSA Code']))
# HRSA matching county components. No sum across repeated designation components.
hpsa=[]
for r in csv.DictReader((RAW/'hrsa_mental_health_hpsa.csv').open()):
 for m in cc:
  if r['Common State County FIPS Code']==m['county_id']:
   hpsa.append(dict(city_id=m['city_id'],**{k:v for k,v in r.items() if k}))
write('hrsa_city_county_components.csv',hpsa)
for c in cities:
 rs=[r for r in hpsa if r['city_id']==c['city_id']]
 for typ in sorted(set(r['Designation Type'] for r in rs)):
  ids={r['HPSA ID'] for r in rs if r['Designation Type']==typ and r['HPSA Status']=='Designated'}
  add(c,'S13','active_mental_hpsa_'+norm(typ),len(ids),'unique designations','2026-11-10 snapshot','city-containing counties',';'.join(m['county_id'] for m in cc if m['city_id']==c['city_id']),'https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_MH.csv','County-component linkage; overlapping designations; type separate; count is background, not shortage population or youth service availability')
# YRBS district geography; counts and CI kept, suppression/missing unchanged.
locmap=dict(zip(['NYC','LO','CH','HO','PH','SA','DA','FW','DU','CM','SF','SE','DN','NS','DCB','CC','BO'],['3651000','0644000','1714000','4835000','4260000','0666000','4819000','4827000','1235000','3712000','0667000','5363000','0820000','4752006','1150000','3240000','2507000']))
yr=[]
for loc,cid in locmap.items():
 p=RAW/f'yrbs_results_{loc}.json'
 if not p.exists():continue
 data=json.loads(p.read_text())
 for r in data:
  yr.append(dict(city_id=cid,**r))
  missing_code = r['MainValue'] if r['MainValue']>100 else None
  missing_note = {888888:'Data not available',333333:'Suppressed: fewer than 30 respondents for subgroup',999999:'Suppressed: fewer than 100 respondents for subgroup'}.get(missing_code,'')
  def estimate(k):
   value=r.get(k)
   return '' if value is not None and value>100 else value
  add(byid[cid],'S12',r['QuestionCode'],estimate('MainValue'),'percent',r['Year'],'school district',loc,'https://youthonline.cdc.gov/','Grades 9-12 district survey; district boundary differs from city; source prevalence direction retained; missing/suppressed not zero; '+missing_note,source_missing_code=missing_code,question=r['QuestionDescription'],sample_size=r.get('SampleSize'),ci_low=estimate('LowConfidenceInterval'),ci_high=estimate('HighConfidenceInterval'),standard_error=estimate('StandardError'))
write('yrbs_district_results_wide.csv',yr)
# FARS exact reported city names except NYC, where all 5 county equivalents jointly equal city.
for p in sorted(RAW.glob('fars_*_national_csv.zip')):
 y=p.name.split('_')[1]
 with zipfile.ZipFile(p) as z:
  an=next(n for n in z.namelist() if n.lower().endswith('/accident.csv') or n.lower()=='accident.csv')
  pn=next(n for n in z.namelist() if n.lower().endswith('/person.csv') or n.lower()=='person.csv')
  ars=list(csv.DictReader(io.TextIOWrapper(z.open(an),encoding='utf-8-sig')))
  cases={};sel=[];agg={c['city_id']:collections.Counter() for c in cities}
  for a in ars:
   for c in cities:
    match=a['STATE'].zfill(2)==c['state_fips'] and norm(a['CITYNAME'])==norm(cname(c))
    if c['city_id']=='3651000':match=a['STATE']=='36' and a['COUNTY'].zfill(3) in ['005','047','061','081','085']
    if match:
     cid=c['city_id'];cases[a['ST_CASE']]=cid;sel.append(dict(city_id=cid,**a));agg[cid]['fatalities']+=int(a['FATALS']);agg[cid]['fatal_crashes']+=1
  write(f'fars_{y}_city_accidents.csv',sel)
  persons=[]
  for r in csv.DictReader(io.TextIOWrapper(z.open(pn),encoding='utf-8-sig')):
   if r['ST_CASE'] not in cases:continue
   cid=cases[r['ST_CASE']]
   if r['INJ_SEV']=='4':
    persons.append(dict(city_id=cid,**r));agg[cid]['person_fatalities']+=1
    if r['PER_TYP']=='5':agg[cid]['pedestrian_fatalities']+=1
    if r['PER_TYP'] in ['6','7']:agg[cid]['pedalcyclist_fatalities']+=1
    if 14<=int(r['AGE'])<=18:agg[cid]['fatalities_age14_18']+=1
  write(f'fars_{y}_city_fatal_persons.csv',persons)
  for c in cities:
   cid=c['city_id'];a=agg[cid]
   assert a['fatalities']==a['person_fatalities'],(y,cid,a)
   gids=sorted({r['STATE']+':'+r['CITY'] for r in sel if r['city_id']==cid})
   for k in ['fatalities','fatal_crashes','pedestrian_fatalities','pedalcyclist_fatalities','fatalities_age14_18']:
    add(c,'S09',k,a[k],'persons' if k!='fatal_crashes' else 'crashes',y,'FARS crash-location city' if cid!='3651000' else 'five NYC county equivalents',';'.join(gids),'https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars','Crash location, not residence; FARS city code boundary may differ from Census balance; 2024 ARF; pedestrian PER_TYP5; pedalcyclist6/7 (2022 coding change); youth14-18 exact')
add(byid['1235000'],'S08-local','murders_local_report',59,'classified murders',2024,'JSO jurisdiction','Jacksonville Sheriff Office','https://www.jaxsheriff.org/Sheriffs-Office/docs/2024-JSO-Annual-Report.aspx','2024 administrative report Homicide Unit p3; 8 pending classifications excluded; local administrative count; not harmonized Table8 total violent offenses')
from collect_safety_health_crime_extract import extend_crime_observations
out=extend_crime_observations(out,cities)
write('city_observations.csv',out)
write('coverage_checks.csv',coverage)
summary=collections.Counter(r['source_id'] for r in out)
print('OBS',len(out),dict(summary),'cities',len({r['city_id'] for r in out}))
