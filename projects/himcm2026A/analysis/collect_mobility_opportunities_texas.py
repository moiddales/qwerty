"""State-source library program values; retain disagreement with federal PLS."""
import pandas as pd
from collect_mobility_opportunities import ROOT,RAW
OUT=ROOT/'data/extracted/mobility_opportunities'
c=pd.read_csv(ROOT/'data/metadata/cities.csv',dtype=str);c=c[c.state_fips.eq('48')]
pg=pd.read_excel(RAW/'texas_pls_2024_datatool.xlsx',sheet_name='24ARPrgms',dtype=str)
fin=pd.read_excel(RAW/'texas_pls_2024_datatool.xlsx',sheet_name='24ARFinData',dtype=str)
x=pd.read_excel(RAW/'texas_pls_2025.xlsx',sheet_name='Texas Central Public Libraries',header=None,dtype=str);headers=x.iloc[0].tolist();codes=[v if isinstance(v,str) else f'unnamed_{i}' for i,v in enumerate(x.iloc[1].tolist())];data=x.iloc[2:];data.columns=codes
obs=[];wide=[]
for city in c.to_dict('records'):
 name=city['city_name'].removesuffix(' city')+' Public Library'
 for yr in [2024,2025]:
  if yr==2024:
   r=pg[pg['Library Name'].str.strip().eq(name)].iloc[0].to_dict();f=fin[fin['Library Name'].str.strip().eq(name)].iloc[0]
   values={'imls_yapro':r['YA Sessions'],'imls_yaatten':r['YA Atten'],'imls_totpro':r['Total Sessions'],'imls_totatten':r['Total Atten']};period=f"FY2024: {f['LFY Start']}--{f['LFY End']}";srcid=r['LIBID'];url='https://www.tsl.texas.gov/sites/default/files/public/tslac/ld/ldn/accreditation/DataTool.xlsx';sheet='24ARPrgms'
  else:
   r=data[data['Q003'].str.strip().eq(name)].iloc[0].to_dict();values={'imls_yapro':r['Q472'],'imls_yaatten':r['Q473'],'imls_totpro':r['Q443'],'imls_totatten':r['Q104']};period='FY2025';srcid=r['ID'];url='https://www.tsl.texas.gov/sites/default/files/public/tslac/ld/ldn/accreditation/statistics/2025AllData.xlsx';sheet='Texas Central Public Libraries'
  wide.append(dict(city_id=city['city_id'],year=yr,sheet=sheet,source_library_id=srcid,**r))
  for ind,v in values.items():obs.append(dict(city_id=city['city_id'],city_name=city['city_name'],state=city['state'],source_id='S20-state',indicator_id=ind,value=v,unit='sessions' if ind.endswith('pro') else 'attendance_visits',observation_period=period,geography_type='library_system',source_geo_id='TexasLibraryID:'+srcid,source_url=url,quality_note=f'State official source, sheet={sheet}. Keep separate from IMLS; FY2024 Fort Worth YA values fill federal -3 source gap. Attendance is visits, not unique youths; shared system areas not city-allocated.'))
pd.DataFrame(obs).to_csv(OUT/'texas_library_program_observations.csv',index=False)
pd.DataFrame(wide).to_csv(OUT/'texas_selected_library_program_wide.csv',index=False)
print('Texas city systems',len(c),'source rows',len(wide),'observations',len(obs))
