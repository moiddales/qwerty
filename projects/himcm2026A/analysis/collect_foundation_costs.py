"""Existing BEA/HUD statistics and historical Opportunity Atlas validation reserve."""
from collect_foundation_extract import CITIES, COUNTIES
from collect_foundation import *
import zipfile, io

def read_hud(path):
    # Official revised 2024 file has an invalid document-property timestamp.
    # Drop only created/modified XML properties in-memory, preserve source bytes.
    if path.name!='FMR2024_final_revised.xlsx': return pd.read_excel(path,dtype=str)
    stream=io.BytesIO()
    with zipfile.ZipFile(path) as z,zipfile.ZipFile(stream,'w') as out:
        for member in z.infolist():
            data=z.read(member.filename)
            if member.filename=='docProps/core.xml':
                data=re.sub(rb'<dcterms:(?:created|modified)[^>]*>.*?</dcterms:(?:created|modified)>',b'',data)
            out.writestr(member,data)
    stream.seek(0)
    return pd.read_excel(stream,dtype=str)

def costs():
    output=[]
    out=EXTRACTED/'costs';out.mkdir(exist_ok=True)
    mapping=COUNTIES[['city_id','cbsa_id','city_population_share_2025']].copy()
    mapping['city_population_share_2025']=mapping.city_population_share_2025.astype(float)
    mapping=mapping.groupby(['city_id','cbsa_id'],as_index=False).city_population_share_2025.sum()
    mapping['principal_cbsa']=mapping.groupby('city_id').city_population_share_2025.transform('max')==mapping.city_population_share_2025
    mapping.to_csv(out/'city_cbsa_population_shares.csv',index=False)
    # Oklahoma City has 0.0118% in the Shawnee micro area, absent from MSA RPP.
    # Use its principal MSA as a regional context, not a weighted city price.
    mapping=mapping[mapping.principal_cbsa]
    with zipfile.ZipFile(RAW/'bea/MARPP.zip') as z:
        for name in z.namelist():
            if not name.endswith('.csv'): continue
            data=pd.read_csv(z.open(name),dtype=str,skipinitialspace=True)
            data['cbsa_id']=data.GeoFIPS.str.strip(' "')
            joined=mapping.merge(data,on='cbsa_id',how='inner')
            assert joined.city_id.nunique()==25
            joined.to_csv(out/name,index=False)
            for r in joined.to_dict('records'):
                for year in range(2008,2025):
                    output.append(dict(city_id=r['city_id'],source_id='S21',indicator_id=r['TableName']+'_'+r['LineCode'],
                        label=r['Description'],value=pd.to_numeric(r[str(year)],errors='coerce'),unit=r['Unit'],
                        observation_period=str(year),source_geography_id=r['cbsa_id'],geography='CBSA regional background',
                        source_file='data/raw/foundation/bea/MARPP.zip#'+name,
                        quality_note='MSA price index; same CBSA cities share values; all-items includes housing'))
    for year,name in [(2024,'FMR2024_final_revised.xlsx'),(2027,'FY27_FMRs.xlsx')]:
        data=read_hud(RAW/'hud'/name)
        data['county_id']=data.fips.str.zfill(10).str[:5]
        # For New England HUD uses town-specific subareas; match Boston, not all Suffolk towns.
        data=data[(data.county_id!='25025') | data.county_town_name.fillna('').str.startswith('Boston')].copy()
        data=data[data.county_id.isin(COUNTIES.county_id)]
        joined=COUNTIES[['city_id','county_id','city_population_share_2025']].merge(data,on='county_id',how='left',validate='many_to_one')
        assert joined.fmr_2.notna().all(),joined[joined.fmr_2.isna()]
        joined['fiscal_year']=year
        joined.to_csv(out/f'HUD_FY{year}_city_county_areas.csv',index=False)
        for r in joined.to_dict('records'):
            for beds in range(5):
                output.append(dict(city_id=r['city_id'],source_id='S22',indicator_id=f'hud_fmr_{beds}br',
                    value=float(r[f'fmr_{beds}']),unit='USD/month',observation_period=f'FY{year}',
                    source_geography_id=r['hud_area_code']+'|'+r['county_id'],geography='HUD rent area linked through county / Boston town',
                    source_file='data/raw/foundation/hud/'+name,quality_note='Rent standard, not observed city rent; FY2027 prospective standard'))
        safmrname='FY27_safmrs.xlsx' if year==2027 else 'fy2024_safmrs_revised.xlsx'
        safmr=read_hud(RAW/'hud'/safmrname)
        safmr.columns=[c.replace('\n',' ').strip() for c in safmr.columns]
        relevant=safmr[safmr['HUD Area Code'].isin(joined.hud_area_code)]
        relevant.to_csv(out/f'HUD_FY{year}_SAFMR_relevant_areas.csv',index=False)
        joined[['city_id','hud_area_code']].drop_duplicates().to_csv(out/f'HUD_FY{year}_city_area_crosswalk.csv',index=False)
    pd.DataFrame(output).to_csv(out/'city_observations.csv',index=False)
    print('BEA/HUD',len(output),'observations',flush=True)

def opportunity():
    out=EXTRACTED/'opportunity';out.mkdir(exist_ok=True)
    counties=set(COUNTIES.county_id)
    for path in sorted((RAW/'opportunity').glob('*.csv')):
        data=pd.read_csv(path,dtype=str)
        if 'county' in data:
            data['county_id']=data.state.str.zfill(2)+data.county.str.zfill(3)
            if 'tract' in data: data['tract_id']=data.county_id+data.tract.str.zfill(6)
        else:
            data['county_id']=data.tract_2020.str.zfill(11).str[:5]
        selected=data[data.county_id.isin(counties)].copy()
        selected.to_csv(out/(path.stem+'_relevant_counties.csv.gz'),index=False,compression='gzip')
        print(path.name,'selected',len(selected),'counties',selected.county_id.nunique(),flush=True)
        if path.name=='county_outcomes_simple.csv':
            joined=COUNTIES[['city_id','county_id','city_population_share_2025']].merge(selected,on='county_id',how='left',validate='many_to_one')
            assert joined.kfr_pooled_pooled_p25.notna().all()
            joined['use']='Historical external validation background only; county is not city; current population shares not historical cohort weights'
            joined.to_csv(out/'city_county_historical_outcomes.csv',index=False)
    (META/'opportunity_scope.md').write_text('''# Historical validation reserve

Source: Opportunity Insights public statistical releases. S26, not S27 (S27 is Dryad).
The 2018-release outcomes describe older birth cohorts; the 2024 late-cohort release has its own codebook. Both files and standard errors/subgroups are preserved. Census-tract identifiers and supplied 2010–2020 crosswalk are not interchangeable with current city boundaries.

County outcomes are existing published statistics linked to each city's constituent counties. These are regional historical background; no county outcome is relabeled a city outcome. Relevant-county tract data are retained for a later explicit spatial crosswalk. No adult outcome is used to set present-day index weights or score values.
''')

if __name__=='__main__':
    {'costs':costs,'opportunity':opportunity}[sys.argv[1]]()
