"""2020-21 state supplements and explicit interval-midpoint safeguards."""
import csv,json
from collect_education_inclusion import BASE,RAW,META
from collect_education_inclusion_extract import OUT,CITY,LONG_FIELDS,write
rows=[]
# OSPI file explicitly SchoolYear2020-21; no year inference needed.
for r in csv.DictReader((RAW/'wa_graduation_2020_21.csv').open()):
 if r['DistrictName']=='Seattle School District No. 1' and r['OrganizationLevel']=='District' and r['Cohort']=='Four Year' and r['StudentGroupType']=='All' and r['StudentGroup']=='All Students':
  c=CITY['5363000'];rows.append(dict(city_id='5363000',city_name=c['city_name'],state=c['state'],source_id='S28',indicator_id='four_year_adjusted_cohort_graduation_rate',value=100*float(r['GraduationRate']),unit='percent',observation_period=r['SchoolYear'],geography_type='whole school district; city proxy',source_geo_id=r['DistrictCode'],source_url='https://data.wa.gov/api/v3/views/rrud-rd4u/export.csv?accessType=DOWNLOAD',quality_note='Official OSPI; Four Year/All Students; cohort='+r['FinalCohort']+'; graduates='+r['Graduate']+'; district not city resident cohort; DataAsOf='+r['DataAsOf'],raw_value=r['GraduationRate']))
# Select exact district, not any record whose postal city says Chicago.
for r in csv.DictReader((OUT/'illinois_2021-RC-Pub-Data-Set_Chicago_graduation.csv').open()):
 if r['Type']=='District' and r['RCDTS']=='150162990250000':
  c=CITY['1714000'];v=r['High School 4-Year Graduation Rate - Total'];rows.append(dict(city_id='1714000',city_name=c['city_name'],state=c['state'],source_id='S28',indicator_id='four_year_adjusted_cohort_graduation_rate',value=v,unit='percent',observation_period='2020-21 (2021 Illinois Report Card)',geography_type='whole City of Chicago SD299; city proxy',source_geo_id=r['RCDTS'],source_url='https://www.isbe.net/_layouts/Download.aspx?SourceUrl=/Documents/2021-RC-Pub-Data-Set.xlsx',quality_note='Exact official field High School 4-Year Graduation Rate - Total; 2021 report edition used as2020-21 supplement; not five-year84%; report edition preserved; source cohort timing methodology should be checked before strict pooled inference',raw_value=v))
assert len(rows)==2
write(OUT/'graduation_2020_21_state_supplements.csv',rows,LONG_FIELDS)
# Urban supplies its own midpoint; never treat as exact rate or use for a minimum guarantee.
p=OUT/'edfacts_2019_20_school_indicators.csv';rs=list(csv.DictReader(p.open()))
for r in rs:
 if r['indicator_id']=='grad_rate_midpt':r['quality_note']='Urban Institute source-provided interval midpoint proxy; NOT an exact observed graduation rate; NOT eligible for minimum/bottom-line constraints. Retain source low/high bounds and suppression; older2019-20 harmonized data.'
write(p,rs,LONG_FIELDS)
coverage=list(csv.DictReader((META/'edfacts_official_city_coverage.csv').open()));have={r['city_id'] for r in coverage if int(r['nonmissing_rate_or_interval'])>0};have.update(r['city_id'] for r in rows)
(META/'graduation_common_year_coverage.json').write_text(json.dumps(dict(period='2020-21; Illinois2021 report edition',cities_with_official_nonmissing_rate_or_interval=sorted(have),count=len(have),note='23 EDFacts cities plus OSPISeattle and ISBEChicago. School/LEA/district geographic units differ; this is data-availability coverage, not25 comparable citywide exact outcomes.'),indent=2))
print(rows);print('coverage',len(have))
