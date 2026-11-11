"""Combine observations without flattening time, geography, or measurement uncertainty."""
from collect_foundation import *

def integrate():
    output=PROJECT/'data/processed';output.mkdir(exist_ok=True)
    selected=[
      'foundation/city_observations.csv','foundation/costs/city_observations.csv',
      'safety_health/city_observations.csv','mobility_opportunities/city_observations.csv',
      'mobility_opportunities/transit_observations.csv','mobility_opportunities/texas_library_program_observations.csv',
      'education_inclusion/education_city_indicators.csv','education_inclusion/ccd_2425_city_indicators.csv',
      'education_inclusion/ccd_2425_grade_enrollment_city_indicators.csv',
      'education_inclusion/hrc_2025_city_policy_indicators.csv','education_inclusion/profiles_local_indicators.csv',
      'education_inclusion/edfacts_official_indicators.csv','education_inclusion/local_graduation_supplement_indicators.csv',
      'education_inclusion/education_core_school_indicators.csv','education_inclusion/edfacts_2019_20_school_indicators.csv',
      'education_inclusion/graduation_2020_21_state_supplements.csv',
      'policy_parameters/youth_transit_policies_25cities.csv','policy_parameters/dc_inclusion_policy_facts.csv']
    for f in (PROJECT/'data/extracted/policy_parameters').glob('*observations*.csv'):
        selected.append(str(f.relative_to(PROJECT/'data/extracted')))
    frames=[];inventory=[]
    for filename in selected:
        path=PROJECT/'data/extracted'/filename
        d=pd.read_csv(path,dtype=str)
        d=d.rename(columns={'geography':'geography_type','source_geography_id':'source_geo_id'})
        d['extracted_file']=str(path.relative_to(PROJECT))
        d['source_row']=range(2,len(d)+2)
        inventory.append(dict(extracted_file=str(path.relative_to(PROJECT)),rows=len(d),
                              nonmissing_numeric_values=pd.to_numeric(d.value,errors='coerce').notna().sum(),cities=d.city_id.nunique()))
        frames.append(d)
    acs=pd.read_csv(EXTRACTED/'acs/city_fields_long.csv.gz',dtype=str).rename(columns={'geography':'geography_type','source_geography_id':'source_geo_id'})
    acs['extracted_file']='data/extracted/foundation/acs/city_fields_long.csv.gz'
    acs['source_row']=range(2,len(acs)+2)
    acs['unit']=acs.table.map({'B19013':'USD','B19113':'USD','B25031':'USD/month','B25064':'USD/month'}).fillna('count; universe in row')
    frames.append(acs)
    cities=pd.read_csv(PROJECT/'data/metadata/cities.csv',dtype=str)
    population=pd.read_csv(EXTRACTED/'population_25cities_2020_2025.csv',dtype=str)
    population=population[['city_id']+[f'POPESTIMATE{y}' for y in range(2020,2026)]].melt(id_vars='city_id',var_name='field',value_name='value')
    population['observation_period']=population.field.str[-4:];population['indicator_id']='population'
    population['unit']='persons';population['source_id']='S01';population['source_geo_id']=population.city_id
    population['geography_type']='Census place/balance';population['quality_note']='Vintage 2025 July 1 estimate'
    population['extracted_file']='data/extracted/foundation/population_25cities_2020_2025.csv'
    frames.append(population)
    master=pd.concat(frames,ignore_index=True,sort=False)
    assert set(master.city_id)==set(cities.city_id)
    master['city_name']=master.city_id.map(cities.set_index('city_id').city_name)
    master['state']=master.city_id.map(cities.set_index('city_id').state)
    master['value']=pd.to_numeric(master.value,errors='coerce')
    master['observation_id']=['obs_'+str(i).zfill(7) for i in range(1,len(master)+1)]
    ordered=['observation_id','city_id','city_name','state','source_id','indicator_id','value','unit','observation_period','geography_type','source_geo_id']
    master=master[ordered+[c for c in master.columns if c not in ordered]]
    master.to_csv(output/'observations_all_levels.csv.gz',index=False,compression='gzip')
    coverage=master.groupby(['city_id','source_id','observation_period','geography_type'],dropna=False).agg(
        rows=('indicator_id','size'),numeric_values=('value','count'),indicators=('indicator_id','nunique')).reset_index()
    coverage.to_csv(PROJECT/'data/metadata/city_source_period_coverage.csv',index=False)
    matrix=master.groupby(['city_id','source_id']).value.count().unstack(fill_value=0)
    matrix=cities[['city_id','city_name']].set_index('city_id').join(matrix)
    matrix.to_csv(PROJECT/'data/metadata/city_source_numeric_coverage.csv')
    dictionary=master.groupby(['source_id','indicator_id','unit','geography_type'],dropna=False).agg(
        rows=('value','size'),numeric_values=('value','count'),cities=('city_id','nunique')).reset_index()
    dictionary.to_csv(PROJECT/'data/metadata/observation_dictionary.csv',index=False)
    detailed=master.groupby(['source_id','indicator_id','unit','observation_period','geography_type','city_id'],dropna=False).value.agg(['count','size'])
    detailed['coverage']=detailed['count'].astype(str)+'/'+detailed['size'].astype(str)
    detailed.coverage.unstack('city_id').reindex(columns=cities.city_id).fillna('0/0').to_csv(PROJECT/'data/metadata/city_indicator_period_coverage.csv')
    pd.DataFrame(inventory).to_csv(PROJECT/'data/metadata/integrated_table_inventory.csv',index=False)
    validation=dict(cities=master.city_id.nunique(),observation_rows=len(master),numeric_values=int(master.value.notna().sum()),
        source_families=master.source_id.nunique(),columns=len(master.columns),
        prohibited_numeric_codes=int((master.value < -100000000).sum()),
        integration='No temporal/geographic aggregation or imputation; observation IDs identify source rows, not independent samples')
    assert validation['prohibited_numeric_codes']==0
    (PROJECT/'data/metadata/integration_validation.json').write_text(json.dumps(validation,indent=2))
    print(json.dumps(validation),flush=True)

if __name__=='__main__':integrate()
