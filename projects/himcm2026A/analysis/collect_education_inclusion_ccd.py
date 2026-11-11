"""CCD current school supply and historic EDFacts graduation; never silently promote vintage."""
import csv,io,zipfile,subprocess,collections,json
from collect_education_inclusion import BASE,RAW,META
from collect_education_inclusion_extract import edge,write,OUT,CITIES,CITY,LONG_FIELDS
loc=edge('2425')
def zipped_rows(path):
 z=zipfile.ZipFile(path);name=next(n for n in z.namelist() if n.lower().endswith('.csv'))
 # NCES large archives use Deflate64, supported by system unzip but not Python zipfile.
 if z.getinfo(name).compress_type==9:
  proc=subprocess.Popen(['unzip','-p',str(path),name],stdout=subprocess.PIPE)
  stream=io.TextIOWrapper(proc.stdout,encoding='utf-8-sig');reader=csv.DictReader(stream)
  yield reader
  stream.close();assert proc.wait()==0
 else:
  stream=io.TextIOWrapper(z.open(name),encoding='utf-8-sig');yield csv.DictReader(stream);stream.close()
 z.close()
high={}
with zipfile.ZipFile(RAW/'ccd_sch_029_2425_w_1a_073025.zip') as z:
 reader=csv.DictReader(io.TextIOWrapper(z.open(next(n for n in z.namelist() if n.endswith('.csv'))),encoding='utf-8-sig'))
 for r in reader:
  if r['NCESSCH'] in loc and any(r['G_'+str(g)+'_OFFERED']=='Yes' for g in [9,10,11,12]) and r['SY_STATUS'] not in ['2','6']:
   high[r['NCESSCH']]=r
write(OUT/'ccd_2425_high_school_crosswalk.csv',[loc[k] for k in high])
stats=[]
for path in sorted(RAW.glob('ccd_sch_*2425*.zip')):
 for reader in zipped_rows(path):
  dest=OUT/'ccd_2425'/path.name.replace('.zip','.csv');dest.parent.mkdir(exist_ok=True)
  count=0
  with dest.open('w',newline='') as f:
   w=csv.DictWriter(f,['city_id']+reader.fieldnames);w.writeheader()
   for r in reader:
    if r['NCESSCH'] in high:
     w.writerow(dict(city_id=loc[r['NCESSCH']]['city_id'],**r));count+=1
  stats.append(dict(source_file=path.name,selected_rows=count,output=str(dest.relative_to(BASE))))
print('CCD',stats,flush=True)
write(META/'ccd_2425_extract_counts.csv',stats)
city_counts=[]
for c in CITIES:
 n=sum(loc[k]['city_id']==c['city_id'] for k in high)
 city_counts.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id='S04',indicator_id='operating_schools_offering_grade9_12',value=n,unit='schools',observation_period='2024-25',geography_type='school points within Census ACS2025 place',source_geo_id=c['city_id'],source_url='https://nces.ed.gov/ccd/Data/zip/ccd_sch_029_2425_w_1a_073025.zip',quality_note='Any grade 9-12 offered; excludes closed and inactive; alternative,charter,virtual flags retained; physical supply not attendance entitlement',raw_value=str(n)))
write(OUT/'ccd_2425_city_indicators.csv',city_counts,LONG_FIELDS)
# Same-year school coordinates for 2019-20 graduation rate data.
gloc=edge('1920');matched=[];long=[];cov=[]
with (RAW/'schools_edfacts_grad_rates_2019.csv').open() as f:
 reader=csv.DictReader(f)
 for r in reader:
  key=r['ncessch'].zfill(12)
  if key not in gloc:continue
  l=gloc[key];matched.append(dict(city_id=l['city_id'],**r))
  if any(r[s]!='99' for s in ['race','lep','homeless','disability','econ_disadvantaged','foster_care']):continue
  for ind in ['cohort_num','grad_rate_low','grad_rate_high','grad_rate_midpt']:
   raw=r[ind];v=raw if raw and not raw.startswith('-') else ''
   long.append(dict(city_id=l['city_id'],city_name=l['city_name'],state=l['state'],source_id='S06',indicator_id=ind,value=v,unit='students' if ind=='cohort_num' else 'percent',observation_period='2019-20',geography_type='school points within Census ACS2025 place using 2019-20 NCES coordinates',source_geo_id=key,source_url='https://educationdata.urban.org/csv/edfacts/schools_edfacts_grad_rates_2019.csv',quality_note='Older version, fallback after official current EDE access failed; Urban Institute harmonized EDFacts; all-student group; midpoint is a source-provided interval midpoint proxy, NOT an exact observed rate and NOT eligible for minimum/bottom-line constraints; retain bounds, cohort and raw suppression codes',raw_value=raw))
write(OUT/'edfacts_2019_20_school_all_groups.csv',matched)
write(OUT/'edfacts_2019_20_school_indicators.csv',long,LONG_FIELDS)
for c in CITIES:
 vals=[r for r in long if r['city_id']==c['city_id'] and r['indicator_id']=='grad_rate_midpt']
 cov.append(dict(city_id=c['city_id'],city_name=c['city_name'],period='2019-20',schools_with_all_student_record=len(vals),schools_with_nonmissing_rate=sum(r['value']!='' for r in vals)))
write(META/'edfacts_city_coverage.csv',cov)
print('EDFacts',len(matched),'subgroup rows',len(long),'long rows',flush=True)
