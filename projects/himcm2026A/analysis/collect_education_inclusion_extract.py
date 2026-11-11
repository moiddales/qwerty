"""Extract all 25 cities; retain raw fields and negative disclosure codes.
School city assignments use NCES coordinates inside official Census ACS2025 polygons.
"""
import csv,io,json,zipfile,re,collections,pathlib,openpyxl
from collect_education_inclusion import BASE,RAW,META
OUT=BASE/'data/extracted/education_inclusion';OUT.mkdir(parents=True,exist_ok=True)
CITIES=list(csv.DictReader((BASE/'data/metadata/cities.csv').open()))
CITY={c['city_id']:c for c in CITIES}
def write(path,rows,fields=None):
 rows=list(rows)
 if not fields:fields=list(rows[0]) if rows else []
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def short(c):
 n=c['city_name'].replace(' city (balance)','').replace(' city','')
 return 'Nashville' if n.startswith('Nashville-Davidson') else n
POLYGON_PATH=BASE/'data/raw/mobility_opportunities/census_acs2025_city_polygons.json'
POLYGONS=[]
for feature in json.loads(POLYGON_PATH.read_text())['features']:
 rings=feature['geometry']['rings']
 pts=[p for ring in rings for p in ring]
 POLYGONS.append((feature['attributes']['GEOID'],rings,(min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts))))
def ring_contains(x,y,ring):
 inside=False
 x1,y1=ring[-1]
 for x2,y2 in ring:
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
  x1,y1=x2,y2
 return inside
def assignment(r):
 try:x,y=float(r[13]),float(r[12])
 except ValueError:return None,None
 for cid,rings,(xmin,ymin,xmax,ymax) in POLYGONS:
  if not (xmin<=x<=xmax and ymin<=y<=ymax):continue
  if sum(ring_contains(x,y,ring) for ring in rings)%2:
   return cid,'school coordinates inside Census TIGERweb ACS2025 place polygon; not attendance eligibility'
 return None,None
def edge(year):
 z=zipfile.ZipFile(RAW/f'ccd_edge_sch_{year}.zip')
 name=next(n for n in z.namelist() if n.upper().endswith('.TXT'))
 out={}
 for r in csv.reader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig'),delimiter='|'):
  cid,note=assignment(r)
  if cid:out[r[0]]=dict(city_id=cid,city_name=CITY[cid]['city_name'],state=CITY[cid]['state'],ncessch=r[0],leaid=r[1],school_name=r[2],school_address=r[4],school_address_city=r[5],school_state=r[6],school_zip=r[7],county_fips=r[9],latitude=r[12],longitude=r[13],observation_period=r[-1],geographic_match=note)
 write(OUT/f'ccd_edge_{year}_city_schools.csv',out.values())
 return out
CORE={'SCH_FTECOUNSELORS':'FTE','SCH_FTESERVICES_PSY':'FTE','SCH_FTESERVICES_SOC':'FTE','SCH_FTESERVICES_NUR':'FTE','SCH_APCOURSES':'courses','SCH_APENR_IND':'yes_no','SCH_IBENR_IND':'yes_no','SCH_DUAL_IND':'yes_no','TOT_APENR_M':'students','TOT_APENR_F':'students','TOT_IBENR_M':'students','TOT_IBENR_F':'students','TOT_DUALENR_M':'students','TOT_DUALENR_F':'students','TOT_ENR_M':'students','TOT_ENR_F':'students'}
LONG_FIELDS=['city_id','city_name','state','source_id','indicator_id','value','unit','observation_period','geography_type','source_geo_id','source_url','quality_note','raw_value']
def extract_crdc_profiles():
 all_long=[];coverage=[];members=[];all_leas=set()
 for year,period,zipname in [('2122','2021-22','crdc_2021_22.zip'),('2324','2023-24','crdc_2023-24-crdc-data.zip')]:
  school=edge(year)
  z=zipfile.ZipFile(RAW/zipname)
  for i in z.infolist():members.append(dict(archive=zipname,member=i.filename,uncompressed_bytes=i.file_size,compressed_bytes=i.compress_size,crc32=hex(i.CRC)))
  chars=csv.DictReader(io.TextIOWrapper(z.open('SCH/School Characteristics.csv'),encoding='utf-8-sig'))
  hs={r['COMBOKEY']:r for r in chars if any(r.get('SCH_GRADE_G'+str(g).zfill(2))=='Yes' for g in [9,10,11,12]) or r.get('SCH_UGDETAIL_HS')=='Yes'}
  wb=openpyxl.load_workbook(RAW/f'crdc_{period}_Appendix_Workbook.xlsx',read_only=True,data_only=True)
  xrows=iter(wb['K. CRDC and EDFacts Crosswalk'].values); headers=next(xrows)
  crosswalk={str(r[0]):dict(zip(headers,r)) for r in xrows}
  ncesfield='NCES SCH '+('2021-22' if year=='2122' else '2023-24')
  matched={}
  used_crosswalk=[]
  for k in hs:
   record=crosswalk.get(k,{})
   nces=record.get(ncesfield)
   if nces and str(nces).zfill(12) in school:
    matched[k]=dict(school[str(nces).zfill(12)],crdc_combokey=k)
    used_crosswalk.append(record)
  leas={hs[k]['LEAID'] for k in matched};all_leas|=leas
  write(OUT/f'crdc_{year}_official_crosswalk_used.csv',used_crosswalk,headers)
  wb.close()
  write(OUT/f'crdc_{year}_high_school_city_crosswalk.csv',matched.values())
  for c in CITIES:
   n=sum(v['city_id']==c['city_id'] for v in matched.values());coverage.append(dict(city_id=c['city_id'],city_name=c['city_name'],source_id='S05',period=period,matched_high_schools=n,geography_note='NCES school point in Census ACS2025 place; includes alternative/virtual/juvenile schools, flags retained; offers any grade 9-12 or ungraded high school'))
  for name in z.namelist():
   if not name.endswith('.csv'):continue
   rows=[]; reader=csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig'))
   for r in reader:
    if name.startswith('LEA/'):
     if r['LEAID'] in leas:rows.append(r)
     continue
    key=r['COMBOKEY']
    if key not in matched:continue
    loc=matched[key]; rows.append(dict(city_id=loc['city_id'],**r))
    for field,unit in CORE.items():
     if field not in r:continue
     raw=r[field];valid=raw!='' and not raw.startswith('-')
     note=loc['geographic_match']+'; school-wide enrollment/staff may cover other grades; public-use student counts privacy protected; raw negative codes retained'
     if not valid:note+='; missing/not applicable/suppressed code '+raw
     all_long.append(dict(city_id=loc['city_id'],city_name=loc['city_name'],state=loc['state'],source_id='S05',indicator_id=field,value=raw if valid else '',unit=unit,observation_period=period,geography_type='school point within Census ACS2025 place',source_geo_id=key,source_url='https://ocrdata.ed.gov/assets/ocr/docs/'+period+'-crdc-data.zip',quality_note=note,raw_value=raw))
   dest=OUT/f'crdc_{year}'/name.replace(' ','_');dest.parent.mkdir(parents=True,exist_ok=True)
   write(dest,rows,['city_id']+reader.fieldnames if name.startswith('SCH/') else reader.fieldnames)
  (META/f'crdc_{year}_national_hs_match_stats.json').write_text(json.dumps(dict(national_high_schools=len(hs),matched_25city_high_schools=len(matched),related_leas=len(leas)),indent=2))
 write(OUT/'education_core_school_indicators.csv',all_long,LONG_FIELDS)
 # Aggregates keep observed denominator and missingness; no suppressed count treated as zero.
 agg=[]
 for c in CITIES:
  for period in ['2021-22','2023-24']:
   for ind in CORE:
    rec=[r for r in all_long if r['city_id']==c['city_id'] and r['observation_period']==period and r['indicator_id']==ind]
    if not rec:continue
    obs=[r for r in rec if r['value']!='']
    unit=CORE[ind]
    value=''
    if obs:
     value=sum(float(r['value']) for r in obs) if unit!='yes_no' else 100*sum(r['value']=='Yes' for r in obs)/len(obs)
    agg.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id='S05',indicator_id=ind+('_offering_percent' if unit=='yes_no' else '_observed_sum'),value=value,unit='percent of responding schools' if unit=='yes_no' else unit,observation_period=period,geography_type='high-school-offering school points within Census ACS2025 place',source_geo_id=c['city_id'],source_url='https://ocrdata.ed.gov/assets/ocr/docs/'+period+'-crdc-data.zip',quality_note='Observed-only aggregate; n_observed='+str(len(obs))+'; n_selected='+str(len(rec))+'; missing/negative codes excluded; staff and enrollment span whole school; not residents or attendance entitlement',raw_value=''))
 write(OUT/'education_city_indicators.csv',agg,LONG_FIELDS)
 write(META/'crdc_city_coverage.csv',coverage)
 write(META/'archive_members.csv',members)
 (META/'related_lea_ids.json').write_text(json.dumps(sorted(all_leas),indent=2))
 # Profiles: preserve all local results and their uncertainty, do not impute nonparticipating cities.
 pr=list(csv.DictReader((RAW/'profiles_2022_2024.csv').open())); local=[];plong=[];pcov=[]
 for c in CITIES:
  name='District of Columbia' if c['city_id']=='1150000' else short(c)
  matches=[r for r in pr if r['LocationType']=='Local' and r['LocationDesc'].split(',')[0]==name]
  for period in ['2022','2024']:
   pcov.append(dict(city_id=c['city_id'],city_name=c['city_name'],period=period,rows=sum(r['Year']==period for r in matches),status='available participating LEA' if any(r['Year']==period for r in matches) else 'not in released local Profiles dataset'))
  for r in matches:
   local.append(dict(city_id=c['city_id'],**r))
   plong.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id='S11',indicator_id=r['PEXCode'],value=r['DataValue'],unit='percent',observation_period=r['Year'],geography_type='participating school district survey, secondary schools',source_geo_id=r['LocationID'],source_url='https://data.cdc.gov/d/yn8z-e2cm',quality_note='Survey of secondary schools; district geography differs from Census place; '+r['DataValueFootnote'],raw_value=r['DataValue']))
 write(OUT/'profiles_local_full_fields.csv',local)
 write(OUT/'profiles_local_indicators.csv',plong,LONG_FIELDS)
 write(META/'profiles_city_coverage.csv',pcov)
 print(json.dumps({'CRDC_core_rows':len(all_long),'Profiles_local_rows':len(local),'cities':len(CITIES),'CRDC_coverage':coverage},indent=2))

if __name__=='__main__': extract_crdc_profiles()
