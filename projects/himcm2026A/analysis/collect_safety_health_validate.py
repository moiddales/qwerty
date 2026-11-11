from collect_safety_health import *
from collections import Counter
rows=list(csv.DictReader((EXT/'city_observations.csv').open()))
assert len({r['city_id'] for r in rows})==25
keys=[tuple(r[k] for k in ['city_id','source_id','indicator_id','observation_period','geography_type','source_geo_id']) for r in rows]
assert len(keys)==len(set(keys)), 'Duplicate observation key'
for r in rows:
 if r['unit']=='percent' and r['value']!='':assert 0<=float(r['value'])<=100,r
 if r['source_id']=='S12' and r['value']!='':
  assert float(r['ci_low'])<=float(r['value'])<=float(r['ci_high']),r
 if r['source_id']=='S08':assert r['reporting_months']=='12'
report={'rows':len(rows),'cities':25,'unique_keys':True,'all_nonmissing_percentages_in_0_100':True,'yrbs_nonmissing_point_estimates_within_ci':True,'fars_accident_and_person_death_totals':'asserted per city-year during extraction','nonmissing_by_source':dict(Counter(r['source_id'] for r in rows if r['value']!='')),'missing_by_source':dict(Counter(r['source_id'] for r in rows if r['value']==''))}
(META/'validation.json').write_text(json.dumps(report,indent=2));print(report)
