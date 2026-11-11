"""Explicit city/year source choices; never silently splice publications into current API."""
from collect_safety_health import *
rows=list(csv.DictReader((EXT/'city_observations.csv').open()))
cities=list(csv.DictReader((BASE/'data/metadata/cities.csv').open()))
choices=[]
for c in cities:
 for y in range(2021,2026):
  candidates=[r for r in rows if r['city_id']==c['city_id'] and r['observation_period']==str(y) and r['indicator_id'] in ['violent_crime','violent_crime_local_definition'] and r['value']!='']
  preferred=next((r for s in ['S08-api','S08-state-CA','S08-local-Chicago','S08-state-NY','S08','S08-local-Phoenix'] for r in candidates if r['source_id']==s),None)
  assert preferred is not None,(c['city_id'],y)
  local=preferred['indicator_id']=='violent_crime_local_definition'
  choices.append(dict(city_id=c['city_id'],city_name=c['city_name'],year=y,selected_source=preferred['source_id'],indicator_id=preferred['indicator_id'],value=preferred['value'],source_geo_id=preferred['source_geo_id'],geography_type=preferred['geography_type'],reporting_months=preferred['reporting_months'],same_current_fbi_series=preferred['source_id']=='S08-api',four_category_definition_eligible=not local,main_common_window=y>=2022,primary_analysis_window=y in [2024,2025],source_url=preferred['source_url'],quality_note=preferred['quality_note'],alternative_sources=';'.join(sorted({r['source_id'] for r in candidates if r['source_id']!=preferred['source_id']}))))
with (EXT/'crime_city_year_source_choice.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=choices[0]);w.writeheader();w.writerows(choices)
print('source choices',len(choices),'same-series',sum(r['same_current_fbi_series'] for r in choices),'four-category',sum(r['four_category_definition_eligible'] for r in choices))
