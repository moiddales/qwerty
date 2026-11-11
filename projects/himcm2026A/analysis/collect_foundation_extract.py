"""Extract all 25 places and relevant county small areas without imputing suppressed cells."""
from collect_foundation import *
import gzip, shutil, zipfile, io

CITIES = pd.read_csv(PROJECT/'data/metadata/cities.csv', dtype=str)
COUNTIES = pd.read_csv(PROJECT/'data/metadata/city_county_cbsa_crosswalk.csv', dtype=str)

def extract_acs():
    out=EXTRACTED/'acs'; out.mkdir(exist_ok=True)
    rows=[]; dictionaries=[]; coverage=[]
    city_ids=set('1600000US'+x for x in CITIES.city_id)
    counties=set(COUNTIES.county_id)
    for file in sorted((RAW/'acs').glob('*YR/*.dat')):
        vintage,period=file.parent.name.split('_'); years=int(period[0])
        table=file.stem.split('-')[1].upper()
        shells=pd.read_csv(RAW/f'acs/ACS{vintage}{period}_Table_Shells.txt',sep='|',dtype=str)
        shell=shells[shells['Table ID']==table].copy()
        shell['source_vintage']=vintage; shell['acs_period']=period
        dictionaries.append(shell)
        labels={int(float(r.Line)):r for r in shell.itertuples() if pd.notna(r.Line)}
        selected=[]; small=[]
        for chunk in pd.read_csv(file,sep='|',dtype=str,chunksize=20000):
            selected.append(chunk[chunk.GEO_ID.isin(city_ids)])
            if years==5:
                ids=chunk.GEO_ID
                small.append(chunk[ids.str.startswith(('1400000US','1500000US')) & ids.str[9:14].isin(counties)])
        data=pd.concat(selected,ignore_index=True)
        actual_cities=len(data)
        absent=city_ids-set(data.GEO_ID)
        assert not set(data.GEO_ID)-city_ids
        data=data.set_index('GEO_ID').reindex(sorted(city_ids)).reset_index()
        data.to_csv(out/f'{vintage}_{period}_{table}_cities.csv',index=False)
        if small:
            areas=pd.concat(small,ignore_index=True)
            areas.to_csv(out/f'{vintage}_{period}_{table}_county_small_areas.csv.gz',index=False,compression='gzip')
        coverage.append(dict(table=table,vintage=vintage,acs_period=period,cities=actual_cities,missing_city_ids=';'.join(sorted(x[9:] for x in absent)),small_area_rows=len(areas) if small else 0))
        for _,r in data.iterrows():
            for field in data.columns:
                if not field.startswith(table+'_E'): continue
                line=int(field.rsplit('E',1)[1]); raw=r[field]; moeraw=r.get(field.replace('_E','_M'),'')
                value=pd.to_numeric(raw,errors='coerce'); moe=pd.to_numeric(moeraw,errors='coerce')
                note=['Place row absent from official summary table'] if r.GEO_ID in absent else []
                if pd.notna(value) and value<0: note.append('estimate_special_code='+str(raw)); value=float('nan')
                if pd.notna(moe) and moe<0: note.append('moe_special_code='+str(moeraw)); moe=float('nan')
                meta=labels.get(line)
                rows.append(dict(city_id=r.GEO_ID[9:],source_id='S02',indicator_id=field,table=table,
                    value=value,moe90=moe,raw_value=raw,raw_moe90=moeraw,
                    observation_period=f'{int(vintage)-years+1}-{vintage}' if years==5 else vintage,
                    vintage=vintage,acs_period=period,source_geography_id=r.GEO_ID,geography='Census place/balance',
                    label=meta.Label if meta else '',universe=meta.Universe if meta else '',
                    source_file=str(file.relative_to(PROJECT)),quality_note=';'.join(note)))
        print(file.name,actual_cities,'cities',flush=True)
    pd.DataFrame(rows).to_csv(out/'city_fields_long.csv.gz',index=False,compression='gzip')
    pd.concat(dictionaries).to_csv(META/'acs_field_dictionary.csv',index=False)
    pd.DataFrame(coverage).to_csv(META/'acs_coverage.csv',index=False)
    # Ratios retain exact numerator/denominator fields; no ungrounded MOE propagation.
    definitions=[
      ('rent_burden_ge30_pct','B25070',[7,8,9,10],list(range(2,11)),'Economic affordability','Renter units with computable burden'),
      ('rent_burden_ge50_pct','B25070',[10],list(range(2,11)),'Economic affordability','Renter units with computable burden'),
      ('no_vehicle_households_pct','B08201',[2],[1],'Mobility background','All households'),
      ('broadband_any_pct','B28002',[4],[1],'Opportunity background','All households; includes cellular-only'),
      ('fixed_broadband_pct','B28002',[7],[1],'Opportunity background','All households'),
      ('no_internet_pct','B28002',[13],[1],'Opportunity background','All households'),
      ('youth16_19_employment_pct','B14005',[4,9,13,18,23,27],[1],'Youth employment background','Population age 16–19'),
      ('enrolled16_19_employment_pct','B14005',[4,18],[3,17],'Youth employment background','Enrolled population age 16–19'),
      ('youth16_19_civilian_employed_share_pct','B23001',[7,93],[3,89],'Youth employment background','Civilian employed numerator / all persons age 16–19 denominator; includes military in denominator'),
      ('youth16_19_school_enrollment_pct','B14005',[3,17],[1],'Education background','Population age 16–19'),
      ('poverty_pct','B17001',[2],[1],'Affordability background','Population with poverty status'),
      ('hispanic_pct','B03003',[3],[1],'Demographic background','Total population; not inclusion score')]
    long=pd.DataFrame(rows); derived=[]
    for (city,vintage,period,table),group in long.groupby(['city_id','vintage','acs_period','table']):
        series=group.set_index('indicator_id').value
        for ident,t,num,den,domain,universe in definitions:
            if t!=table: continue
            nf=[f'{table}_E{i:03d}' for i in num];df=[f'{table}_E{i:03d}' for i in den]
            numerator=series.reindex(nf).sum(min_count=len(nf));denominator=series.reindex(df).sum(min_count=len(df))
            derived.append(dict(city_id=city,source_id='S02',indicator_id=ident,domain=domain,
                observation_period=group.observation_period.iloc[0],vintage=vintage,acs_period=period,
                value=100*numerator/denominator if denominator>0 else float('nan'),unit='percent',
                numerator=numerator,denominator=denominator,numerator_fields='+'.join(nf),denominator_fields='+'.join(df),
                age_universe=universe,geography='Census place/balance',source_file=group.source_file.iloc[0],
                quality_note='Derived MOE not calculated; component MOEs preserved; do not assume independence'))
    result=pd.DataFrame(derived)
    assert result.value.dropna().between(0,100).all()
    result.to_csv(EXTRACTED/'city_observations.csv',index=False)
    print('ACS long fields',len(rows),'derived',len(result),flush=True)

def inspect_costs():
    with zipfile.ZipFile(RAW/'bea/MARPP.zip') as z:
        print('BEA',z.namelist())
        for n in z.namelist():
            if n.lower().endswith('.csv'): print(n,z.read(n)[:1500].decode('utf-8-sig','replace'))
    for n in ['FY27_FMRs.xlsx','FMR2024_final_revised.xlsx','FY27_safmrs.xlsx','fy2024_safmrs_revised.xlsx']:
        p=RAW/'hud'/n; x=pd.ExcelFile(p);print(n,x.sheet_names)
        print(pd.read_excel(p,nrows=3).to_string(index=False))
    for p in (RAW/'opportunity').glob('*.csv'):
        print(p.name,pd.read_csv(p,nrows=2).to_string(index=False)[:3500])

if __name__=='__main__':
    {'acs':extract_acs,'inspect':inspect_costs}[sys.argv[1]]()
