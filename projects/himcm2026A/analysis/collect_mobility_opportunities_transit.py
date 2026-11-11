"""Select principal transit providers associated with each city; retain agency geography."""
import json,pandas as pd
from collect_mobility_opportunities import ROOT,RAW,META
OUT=ROOT/'data/extracted/mobility_opportunities'
c=pd.read_csv(ROOT/'data/metadata/cities.csv',dtype=str)
# These are principal-provider associations, not complete provider inventories or allocations.
ids=['20008','90154','50066','60008','90032','30019','60011','90026','60056','60007','40040','60048','90013','40008','50016','50050','90015','00001','80006','40004','60017','30030','60006','90045','10003']
a=pd.read_csv(RAW/'ntd_2025_agencies.csv',dtype=str,keep_default_na=False)
service=pd.read_csv(RAW/'ntd_2022_2025_service.csv',dtype=str,keep_default_na=False)
maprows=[];full=[];obs=[]
for city,ntdid in zip(c.to_dict('records'),ids):
 ar=a[a['NTD ID'].eq(ntdid)].iloc[0].to_dict()
 maprows.append(dict(city_id=city['city_id'],city_name=city['city_name'],association='principal provider; not exhaustive; no city allocation',**ar))
 for r in service[service['NTD ID'].eq(ntdid)].to_dict('records'):
  full.append(dict(city_id=city['city_id'],associated_city_name=city['city_name'],**r))
  if r['Time Period']!='Annual Total':continue
  for field,ind,unit in [('Actual Vehicle/Passenger Car Revenue Miles','ntd_annual_revenue_miles','vehicle_passenger_car_miles'),('Actual Vehicle/Passenger Car Revenue Hours','ntd_annual_revenue_hours','vehicle_passenger_car_hours'),('Unlinked Passenger Trips (UPT)','ntd_annual_unlinked_trips','boardings')]:
   obs.append(dict(city_id=city['city_id'],city_name=city['city_name'],state=city['state'],source_id='S17',indicator_id=ind,value=r[field].replace(',',''),unit=unit,observation_period=r['Report Year'],geography_type='transit_agency_mode_service',source_geo_id=f"{ntdid}|{r['Mode']}|{r['Type Of Service']}",source_url='https://data.transportation.gov/d/wwdp-t4re',quality_note=f"Principal provider association, no city allocation; mode={r['Mode Name']}; service area population={r['Service Area Population']}; UZA={r['UZA Name']}. Trips include all ages; cars counted individually for rail. Questionable flags retained in wide table."))
pd.DataFrame(maprows).to_csv(OUT/'city_principal_transit_provider_associations.csv',index=False)
pd.DataFrame(full).to_csv(OUT/'ntd_associated_provider_service_2022_2025.csv',index=False)
pd.DataFrame(obs).to_csv(OUT/'transit_observations.csv',index=False)
for kind in ['stops','routes']:
 data=pd.read_csv(OUT/f'bts_ntm_{kind}_agency_counts.csv',dtype=str);data['source_ntd_ids']=data.ntd_id;data['ntd_id']=data.ntd_id.fillna('').str.split(';');data=data.explode('ntd_id');data['ntd_id']=data.ntd_id.str.zfill(5)
 data['quality_note']='Feed can list several NTD IDs; record_count describes shared feed, not agency-exclusive or city total; do not sum duplicated feed counts.'
 data.merge(pd.DataFrame({'city_id':c.city_id,'ntd_id':ids}),on='ntd_id',how='inner').to_csv(OUT/f'bts_ntm_{kind}_associated_agency_counts.csv',index=False)
print('providers',len(maprows),'service rows',len(full),'observations',len(obs),'years',service['Report Year'].value_counts().to_dict())
