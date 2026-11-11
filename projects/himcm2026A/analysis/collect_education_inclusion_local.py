"""Official state/district supplements for the two cities absent in EDFacts 2020-21."""
import csv,re,json,openpyxl
from collect_education_inclusion import BASE,RAW,META
from collect_education_inclusion_extract import OUT,CITY,LONG_FIELDS,write
long=[]
logs=[json.loads(x) for x in (META/'access_log.jsonl').read_text().splitlines()]
urls={x['local_path'].split('/')[-1]:x['url'] for x in logs if x.get('status')=='downloaded'}
def add(cid,ind,val,unit,period,gid,url,note,raw=None):
 c=CITY[cid];long.append(dict(city_id=cid,city_name=c['city_name'],state=c['state'],source_id='S28',indicator_id=ind,value=val if val is not None else '',unit=unit,observation_period=period,geography_type='whole school district official outcome; geographic proxy',source_geo_id=gid,source_url=url,quality_note=note,raw_value=str(raw if raw is not None else val)))
for name in ['wa_graduation_2020_21.csv','wa_graduation_2023_24.csv','wa_graduation_2024_25.csv']:
 rows=[r for r in csv.DictReader((RAW/name).open()) if r['DistrictName']=='Seattle School District No. 1']
 write(OUT/name.replace('wa_','seattle_'),[dict(city_id='5363000',**r) for r in rows])
 for r in rows:
  if r['OrganizationLevel']!='District' or r['Cohort']!='Four Year' or r['StudentGroupType']!='All' or r['StudentGroup']!='All Students':continue
  for k,unit in [('GraduationRate','percent'),('FinalCohort','students'),('Graduate','students')]:
   raw=r[k];val='' if raw in ['', 'NULL'] else (100*float(raw) if k=='GraduationRate' else float(raw.replace(',','')))
   add('5363000','OSPI_4year_'+k,val,unit,r['SchoolYear'],r['DistrictCode'],urls[name],'Seattle School District No. 1; school/district records and all groups retained; rate source is fraction converted to percent; suppression flags retained',raw)
# JSON objects embedded by official CPS page support its own charts; extract district only.
s=(RAW/'cps_graduation_page.html').read_text();objects=[]
for m in re.finditer(r'data\.district\s*=\s*',s):
 obj,end=json.JSONDecoder().raw_decode(s[m.end():]);objects.append(obj)
assert objects,'No CPS district object found'
flat=[]
for obj in objects:
 for year in obj['SchoolYears']:
  for r in year['Categories']:
   flat.append(dict(city_id='1714000',metric=obj['MetricTitle'],school_year=year['SchoolYear'],**r))
   if '4-Year' not in obj['MetricTitle'] or r['Category']!='ALL':continue
   for k,unit in [('Rate','percent'),('Numerator','students'),('Denominator','students')]:
    add('1714000','CPS_4year_'+k,r[k],unit,year['SchoolYear'],'CPS District',urls['cps_graduation_page.html'],'Official CPS district chart data; cohort methodology described on page; whole district proxy, includes students starting in ninth grade who graduated from CPS schools')
write(OUT/'cps_graduation_2023_2025_all_groups.csv',flat)
# ISBE originals offer broad background plus older same-year graduation evidence.
for file in sorted(RAW.glob('illinois_*Data-Set.xlsx')):
 wb=openpyxl.load_workbook(file,read_only=True,data_only=True)
 if 'General' not in wb.sheetnames:
  (META/(file.stem+'_sheets.json')).write_text(json.dumps(wb.sheetnames));wb.close();continue
 it=iter(wb['General'].values);head=next(it);selected=[];selected_fields=[h for h in head if h and ('Graduat' in str(h) or h in ['RCDTS','Type','Level','School Name','District','City','County','Grades Served'])]
 for r in it:
  x=dict(zip(head,r))
  if x.get('City')!='Chicago' and x.get('District') not in ['City of Chicago SD 299','Chicago Public Schools District 299']:continue
  y=dict(city_id='1714000',**{h:x[h] for h in selected_fields});selected.append(y)
 write(OUT/(file.stem+'_Chicago_graduation.csv'),selected,['city_id']+selected_fields)
 wb.close()
write(OUT/'local_graduation_supplement_indicators.csv',long,LONG_FIELDS)
print('Local supplement long rows',len(long))
