"""Extend observations with current FBI monthly series and independently downloaded state/local tables."""
from collect_safety_health import *
from collections import defaultdict

def extend_crime_observations(out,cities):
 byid={c['city_id']:c for c in cities};monthly=[];annual=[];checks=[]
 ag=list(csv.DictReader((EXT/'fbi_city_agency_registry_crosswalk.csv').open()))
 indicators={'homicide':'murder','rape':'rape','robbery':'robbery','aggravated-assault':'aggravated_assault','violent-crime':'violent_crime'}
 def add(c,s,indicator,value,year,geo,gid,url,note,**extra):
  out.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id=s,indicator_id=indicator,value=value,unit='reported offenses',observation_period=year,geography_type=geo,source_geo_id=gid,source_url=url,quality_note=note,**extra))
 for a in ag:
  c=byid[a['city_id']];byyear=defaultdict(dict)
  for offense,indicator in indicators.items():
   f=RAW/f"fbi_monthly_{a['ori']}_{offense}_2021_2025.json"
   d=json.loads(f.read_text())
   url=f"https://cde.ucr.cjis.gov/LATEST/summarized/agency/{a['ori']}/{offense}?from=01-2021&to=12-2025&type=counts"
   actual=d['offenses']['actuals'];k=next(k for k in actual if k.endswith(' Offenses'));name=k.removesuffix(' Offenses')
   pops=d['populations']['population'][name];participated=d['populations']['participated_population'][name]
   refresh=d['cde_properties']['last_refresh_date']['UCR']
   for period,v in actual[k].items():
    pp=participated.get(period);pop=pops.get(period)
    monthly.append(dict(city_id=c['city_id'],ori=a['ori'],agency_name=name,indicator_id=indicator,period=period,actual_count=v,agency_population=pop,participated_population=pp,coverage_percent=100*pp/pop if pop and pp is not None else '',source_url=url,last_refresh_date=refresh))
   for y in range(2021,2026):
    rs=[r for r in monthly if r['city_id']==c['city_id'] and r['indicator_id']==indicator and r['period'].endswith(str(y))]
    reported=[r for r in rs if r['actual_count'] is not None and r['participated_population'] is not None and r['participated_population']>0]
    total=sum(r['actual_count'] for r in reported) if len(reported)==12 else ''
    popvals=sorted({r['agency_population'] for r in rs if r['agency_population'] is not None})
    byyear[y][indicator]=total
    note='Current FBI monthly summarized counts; source refresh '+refresh+'; annual sum only for 12 nonmissing months with participated population>0; publication Table8 kept as a separate snapshot; agency geography, not verified Census boundary; no city-population denominator substitution'
    annual.append(dict(city_id=c['city_id'],ori=a['ori'],agency_name=name,year=y,indicator_id=indicator,annual_count=total,reported_months=len(reported),agency_population_min=min(popvals) if popvals else '',agency_population_max=max(popvals) if popvals else '',last_refresh_date=refresh,quality_note=note))
    add(c,'S08-api',indicator,total,y,'police agency',a['ori'],url,note,reporting_months=len(reported),agency_population=min(popvals) if len(popvals)==1 else '',population_min=min(popvals) if popvals else '',population_max=max(popvals) if popvals else '',source_refresh_date=refresh)
  for y,values in byyear.items():
   complete=all(v!='' for v in values.values())
   equality=values['violent_crime']==sum(values[k] for k in ['murder','rape','robbery','aggravated_assault']) if complete else None
   checks.append(dict(city_id=c['city_id'],year=y,all_five_complete=complete,violent_equals_four_components=equality,**values))
 def write(n,rs):
  with (EXT/n).open('w',newline='') as h:
   w=csv.DictWriter(h,fieldnames=list(dict.fromkeys(k for r in rs for k in r)));w.writeheader();w.writerows(rs)
 write('fbi_current_monthly_counts_25cities.csv',monthly);write('fbi_current_annual_counts_25cities.csv',annual);write('fbi_current_annual_component_checks.csv',checks)
 # NY DCJS county totals: the five borough county equivalents jointly cover New York City.
 ny=list(csv.DictReader((RAW/'nyc_index_crimes_2021_2025.csv').open()))
 for year in sorted({r['year'] for r in ny}):
  rs=[r for r in ny if r['year']==year]
  assert {r['county'] for r in rs}=={'Bronx','Kings','New York','Queens','Richmond'}
  assert all(r['months_reported']=='12' for r in rs)
  for sourcefield,indicator in [('violent','violent_crime'),('murder','murder'),('forcible_rape','rape'),('robbery','robbery'),('aggravated_assault','aggravated_assault')]:
   add(byid['3651000'],'S08-state-NY',indicator,sum(int(r[sourcefield]) for r in rs),year,'five NYC county equivalents','36005;36047;36061;36081;36085','https://data.ny.gov/resource/ca8h-8gjq.csv','NY DCJS current published index crimes; five County Total rows, 12 months each; state reporting definitions and vintage retained',reporting_months=12)
 # Phoenix annual SRS table independently downloaded from current official city page; 2021 column.
 for indicator,value in [('homicide_including_negligent',198),('rape',1087),('robbery',3183),('aggravated_assault',8657),('violent_crime_local_definition',13125)]:
  add(byid['0455000'],'S08-local-Phoenix',indicator,value,2021,'police agency','AZ0072300','https://www.phoenix.gov/content/dam/phoenix/policesite/documents/crime-stats-and-maps/ucr_2010-2022.pdf','2021 column in Phoenix UCR SRS annual 2010-2022 table, page1; source homicide explicitly includes manslaughter by negligence; total therefore not harmonized with FBI violent crime; published SRS snapshot, not current API snapshot',reporting_months=12)
 # CA DOJ published statewide annual agency table; preserve full selected rows.
 ca=list(csv.DictReader((RAW/'ca_Crimes_and_Clearances_with_Arson-1985-2025.csv').open()))
 selected=[]
 for c in cities:
  if c['state_abbr']!='CA':continue
  name=c['city_name'].removesuffix(' city')
  rs=[r for r in ca if r['NCICCode']==name and 2021<=int(r['Year'])<=2025]
  assert len(rs)==5,(name,len(rs))
  for r in rs:
   selected.append(dict(city_id=c['city_id'],**r))
   assert int(r['Violent_sum'])==sum(int(r[k]) for k in ['Homicide_sum','ForRape_sum','Robbery_sum','AggAssault_sum'])
   for field,indicator in [('Violent_sum','violent_crime'),('Homicide_sum','murder'),('ForRape_sum','rape'),('Robbery_sum','robbery'),('AggAssault_sum','aggravated_assault')]:
    add(c,'S08-state-CA',indicator,r[field],r['Year'],'state-defined police jurisdiction',name,'https://data-openjustice.doj.ca.gov/sites/default/files/dataset/2026-07/Crimes_and_Clearances_with_Arson-1985-2025.csv','CA DOJ July2026 release; annual published agency table; 2021 onward combines SRS and converted IBR; rape reporting definitions differ before2025, see June2026 context; annual file has no months-reported field; blank reporting_months means unverified, not zero',reporting_months='')
 write('ca_crime_selected_jurisdictions_2021_2025.csv',selected)
 # Chicago annual report: printed p77 and definitions p74; exclude human trafficking.
 for indicator,value in [('murder',800),('rape',1648),('robbery',7925),('aggravated_assault',7237+8369),('violent_crime',800+1648+7925+7237+8369)]:
  add(byid['1714000'],'S08-local-Chicago',indicator,value,2021,'police agency','ILCPD0000','https://www.chicagopolice.org/wp-content/uploads/legacy/2021-Annual-Report.pdf','CPD 2021 annual report printed p77 (PDF79), UCR category definitions p74; aggravated assault plus aggravated battery; four-category violent sum excludes 17 human trafficking offenses included in local violent index subtotal; incident counts, annual publication snapshot',reporting_months=12)
 print('FBI monthly:' ,len(monthly),'annual:',len(annual),'complete city-years:',sum(r['all_five_complete'] for r in checks),'component mismatches:',sum(r['violent_equals_four_components'] is False for r in checks))
 return out
