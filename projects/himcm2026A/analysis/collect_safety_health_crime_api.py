"""Latest official FBI monthly offense counts and participation, all 25 agencies.
Published Table8 vintage remains separate; annual totals require 12 nonmissing months.
"""
from collect_safety_health import *
agencies=list(csv.DictReader((EXT/'fbi_city_agency_registry_crosswalk.csv').open()))
items=[]
for a in agencies:
 for off in ['homicide','rape','robbery','aggravated-assault','violent-crime']:
  ori=a['ori'];n=f'fbi_monthly_{ori}_{off}_2021_2025.json'
  items.append(('S08-api',f'https://cde.ucr.cjis.gov/LATEST/summarized/agency/{ori}/{off}?from=01-2021&to=12-2025&type=counts',n,'police agency','2021-2025 monthly; current snapshot'))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:list(ex.map(fetch,items))
