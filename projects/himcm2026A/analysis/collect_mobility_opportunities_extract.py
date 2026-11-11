"""Extract source observations, retaining library-system geography and boundary sensitivity."""
import csv,json,pathlib,zipfile,gzip
import pandas as pd
from collect_mobility_opportunities import ROOT,RAW,META
OUT=ROOT/'data/extracted/mobility_opportunities'
cities=pd.read_csv(ROOT/'data/metadata/cities.csv',dtype=str).to_dict('records')
rows=[]
def obs(c,source,indicator,value,unit,period,geography,geoid,url,note):
 rows.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id=source,indicator_id=indicator,value=value,unit=unit,observation_period=period,geography_type=geography,source_geo_id=geoid,source_url=url,quality_note=note))
# Curated principal public systems. Association does not allocate system totals to the city.
keys=['NY0004|NY0562|NY0778','CA0063','IL0098','TX0099','AZ0035','PA0385','TX0263','CA0113','TX0003','TX0050','FL0003','TX0111','CA0115','NC0045','OH0057','IN0210','CA0114','WA0064','CO0034','TN0135','OK0074','DC0001','TX0030','NV0008','MA0035']
fields=['POPU_LSA','CENTLIB','BRANLIB','HRS_OPEN','YAPRO','YAATTEN','TOTPRO','TOTATTEN','GPTERMS']
wide=[];outlets=[];inventory=[]
for yr in [2023,2024]:
 z=zipfile.ZipFile(RAW/f'imls_pls_fy{yr}_csv.zip')
 ae=pd.read_csv(z.open(next(n for n in z.namelist() if '_AE_' in n and n.endswith('.csv'))),dtype=str,encoding='cp1252',keep_default_na=False)
 ot=pd.read_csv(z.open(next(n for n in z.namelist() if 'outlet' in n and n.endswith('.csv'))),dtype=str,encoding='cp1252',keep_default_na=False)
 inventory.extend([{'file':f'imls_pls_fy{yr}_csv.zip:AE','rows':len(ae),'columns':len(ae.columns)},{'file':f'imls_pls_fy{yr}_csv.zip:outlets','rows':len(ot),'columns':len(ot.columns)}])
 for c,ks in zip(cities,keys):
  for key in ks.split('|'):
   r=ae[ae.FSCSKEY.eq(key)].iloc[0].to_dict()
   wide.append(dict(city_id=c['city_id'],city_name=c['city_name'],observation_period=f'FY{yr}',**r))
   note=f"Associated public library system; no allocation to city. LSA={r['LSAGEOTYPE']} {r['LSAGEOID']}; GEOCODE={r['GEOCODE']}; LSA/census population ratio={r['LSAGEORATIO']}. YA targets ages12-18; synchronous in-person/virtual sessions; attendance is visits, not unique youths."
   for f in fields:
    v=r[f];valid=v not in ['','M'] and float(v)>=0
    obs(c,'S20',f'imls_{f.lower()}',v if valid else '', 'people' if f=='POPU_LSA' else 'attendance_visits' if 'ATTEN' in f else 'sessions' if 'PRO' in f else 'hours' if f=='HRS_OPEN' else 'count',f'FY{yr}: {r["STARTDAT"]}--{r["ENDDATE"]}','library_system',key,'https://www.imls.gov/research-evaluation/surveys/public-libraries-survey-pls',note+f' Raw value={v}; imputation flags retained in wide source table.')
   for r2 in ot[ot.FSCSKEY.eq(key)].to_dict('records'):outlets.append(dict(city_id=c['city_id'],associated_city_name=c['city_name'],observation_period=f'FY{yr}',**r2))
pd.DataFrame(wide).to_csv(OUT/'imls_associated_systems_2023_2024.csv',index=False)
pd.DataFrame(outlets).to_csv(OUT/'imls_associated_system_outlets_2023_2024.csv',index=False)
# Source values quoted as facts only; copyrighted PDF/package is not redistributed.
park=[99,62,98,65,50,97,47,82,81,73,35,76,79,40,None,None,100,99,96,44,41,99,66,None,100]
for c,v in zip(cities,park):
 note='Numerical fact transcribed from published 2026 ParkScore PDF; rounded percent; original restricted package not archived.'
 geo='TPL reported city'
 if c['city_id'] in ['3712000','4752006']:geo='TPL reported city-county';note+=' Source reports Charlotte-Mecklenburg County or Nashville-Davidson County; not Census place/balance exact boundary.'
 if v is None:note+=' Unresolved: Columbus/Indianapolis not identified in this PDF; Las Vegas conflicts with Louisville row label; verify other official tables.'
 url='https://parkserve.tpl.org/downloads/historic/2026_ParkScoreRank.pdf';period='2026 release'
 if v is None:
  alt={'3918000':(71,'columbus-ohio'),'1836003':(36,'indianapolis-city-balance-indiana'),'3240000':(70,'las-vegas-nevada')}
  v,slug=alt[c['city_id']];url='https://www.tpl.org/city/'+slug;period='website snapshot 2026-11-11; measurement vintage unconfirmed';geo='TPL reported Census place/balance';note='Numerical fact cited from official city page; 2026 PDF gap/label conflict resolved with separate snapshot, not relabeled as 2026 measurement. Original restricted webpage/package not redistributed.'
 obs(c,'S19','park_residents_within_10min_walk',v,'percent',period,geo,c['city_name'],url,note)
# SLD derived means for fully-contained and intersecting BG sets. Both are explicit spatial proxies.
sld=pd.read_csv(RAW/'epa_sld_v3_2021.csv',dtype={'GEOID20':str,'GEOID10':str},low_memory=False)
inventory.append({'file':'epa_sld_v3_2021.csv','rows':len(sld),'columns':len(sld.columns)})
# Official CSV truncates many GEOIDs in scientific notation; recover exact 2019 ID from the intact component fields.
sld['GEOID20']=sld.STATEFP.astype(int).astype(str).str.zfill(2)+sld.COUNTYFP.astype(int).astype(str).str.zfill(3)+sld.TRACTCE.astype(int).astype(str).str.zfill(6)+sld.BLKGRPCE.astype(int).astype(str)
assert sld.GEOID20.is_unique, 'component-derived BG IDs must be unique'
coverage=[];bgmap=[]
for c in cities:
 for selection in ['contained','intersecting']:
  files=list(RAW.glob(f'epa_sld_{c["city_id"]}_{selection}*.json'))
  if c['city_id']=='3651000': files=list(RAW.glob(f'epa_nyc_{selection}_validated_*.json'))
  ids=[]
  for file in files:
   j=json.loads(file.read_text());ids += [str(f['attributes']['GEOID20']).zfill(12) for f in j.get('features',[])]
  unique=set(ids)
  x=sld[sld.GEOID20.isin(unique)]
  coverage.append(dict(city_id=c['city_id'],selection=selection,selected_bg=len(unique),raw_records=len(ids),matched_bg=len(x),sld_population=x.TotPop.sum()))
  bgmap.extend(dict(city_id=c['city_id'],bg_geoid2019=k,selection=selection,boundary_version='ACS2025') for k in unique)
  for f,unit in [('NatWalkInd','index_1_20'),('D3B','weighted_intersections_per_sq_mile'),('D4A','meters'),('D4C','peak_hour_service_frequency')]:
   valid=x[(x[f]>=0)&(x.TotPop>0)];w=valid.TotPop;value=(valid[f]*w).sum()/w.sum() if w.sum()>0 else ''
   note=f'Population-weighted {selection} 2019 BG set selected by EPA spatial service against ACS2025 place polygons; partial BG allocation unresolved. Mixed source years (2014-2018 ACS population; 2020 transit). Valid population={w.sum()}; selected population={x.TotPop.sum()}. Negative sentinels excluded, not converted to zero; missing transit can indicate threshold/coverage.'
   obs(c,'S16',f'sld_{f.lower()}_{selection}_bg_proxy',value,unit,'SLD V3 2021 release; mixed inputs',f'{selection} BG subset environmental proxy',c['city_id'],'https://edg.epa.gov/EPADataCommons/public/OA/EPA_SmartLocationDatabase_V3_Jan_2021_Final.csv',note)
pd.DataFrame(coverage).to_csv(OUT/'sld_city_boundary_coverage.csv',index=False)
pd.DataFrame(bgmap).to_csv(OUT/'sld_city_bg_spatial_selection.csv',index=False)
# NTD annual supply and day-type rows retained at agency/mode/TOS level.
ntd=pd.read_csv(RAW/'ntd_2025_service.csv',dtype=str,keep_default_na=False)
inventory.append({'file':'ntd_2025_service.csv','rows':len(ntd),'columns':len(ntd.columns)})
ntd[ntd['Time Period'].eq('Annual Total')].to_csv(OUT/'ntd_2025_service_annual_agency_mode.csv',index=False)
for kind in ['stops','routes']:
 j=json.loads((RAW/f'bts_ntm_{kind}_agency_counts.json').read_text())
 assert not j.get('exceededTransferLimit'),kind
 df=pd.DataFrame(f['attributes'] for f in j['features']);df.to_csv(OUT/f'bts_ntm_{kind}_agency_counts.csv',index=False)
 inventory.append({'file':f'bts_ntm_{kind}_agency_counts.json','rows':len(df),'source_records_counted':int(df.record_count.sum())})
pd.DataFrame(rows).to_csv(OUT/'city_observations.csv',index=False)
pd.DataFrame(inventory).to_csv(META/'table_inventory.csv',index=False)
print('observations',len(rows),'cities',len(set(r['city_id'] for r in rows)),'library systems',len(wide),'outlets',len(outlets));print(pd.DataFrame(coverage).to_string(index=False))
