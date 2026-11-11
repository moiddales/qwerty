"""School grade enrollment aggregates; exact published subtotals only."""
import csv,collections
from collect_education_inclusion import BASE
from collect_education_inclusion_extract import OUT,META,CITIES,LONG_FIELDS,write
path=OUT/'ccd_2425/ccd_sch_052_2425_l_1a_073025.csv'
sums=collections.defaultdict(float);n=collections.Counter();missing=collections.Counter();per_school=[]
for r in csv.DictReader(path.open()):
 if r['TOTAL_INDICATOR']!='Subtotal 4 - By Grade' or r['RACE_ETHNICITY']!='No Category Codes' or r['SEX']!='No Category Codes' or r['GRADE'] not in ['Grade 9','Grade 10','Grade 11','Grade 12']:continue
 per_school.append(r);k=(r['city_id'],r['GRADE']);raw=r['STUDENT_COUNT']
 if raw and float(raw)>=0:sums[k]+=float(raw);n[k]+=1
 else:missing[k]+=1
rows=[]
for c in CITIES:
 for grade in ['Grade 9','Grade 10','Grade 11','Grade 12']:
  k=c['city_id'],grade
  rows.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id='S04',indicator_id='enrollment_'+grade.replace(' ','_').lower(),value=sums[k] if n[k] else '',unit='students',observation_period='2024-25',geography_type='schools within Census ACS2025 place, physical supply',source_geo_id=c['city_id'],source_url='https://nces.ed.gov/ccd/Data/zip/ccd_sch_052_2425_l_1a_073025.zip',quality_note='Published grade subtotal across selected operating schools; school enrollment not resident count; observed school rows='+str(n[k])+'; missing rows='+str(missing[k])+'; excluded race/sex subtotals to avoid double counting',raw_value=''))
write(OUT/'ccd_2425_grade_enrollment_city_indicators.csv',rows,LONG_FIELDS)
write(OUT/'ccd_2425_high_school_grade_subtotals.csv',per_school)
print('City grade rows',len(rows),'School grade subtotals',len(per_school))
