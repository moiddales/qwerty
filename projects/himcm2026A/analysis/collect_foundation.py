"""Collect population, ACS, costs and geography from existing public datasets."""
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from datetime import datetime, timezone
import csv, hashlib, json, re, sys, time
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

PROJECT = Path(__file__).resolve().parents[1]
RAW = PROJECT / 'data/raw/foundation'
META = PROJECT / 'data/metadata/foundation'
EXTRACTED = PROJECT / 'data/extracted/foundation'
for directory in (RAW, META, EXTRACTED, META/'access'):
    directory.mkdir(parents=True, exist_ok=True)

def fetch(url, name, source_id, period='', kind='file', note=''):
    """Persist an actual response and its provenance; report access failures explicitly."""
    destination = RAW / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    record = dict(source_id=source_id, url=url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                  observation_period=period, source_file=str(destination.relative_to(PROJECT)),
                  note=note, access_channel='runtime urllib HTTPS', license='US federal government source; retain source attribution')
    try:
        with urlopen(Request(url, headers={'User-Agent':'HiMCMResearch/1.0'}), timeout=60) as response:
            record.update(http_status=response.status, final_url=response.url, content_type=response.headers.get('Content-Type'))
            first=response.read(4096)
            if kind!='html' and (b'<html' in first.lower() or b'<!doctype html' in first.lower()):
                record.update(status='unexpected_html', response_excerpt=first[:350].decode('utf-8','replace'))
            else:
                digest=hashlib.sha256()
                with destination.open('wb') as stream:
                    chunk=first
                    while chunk:
                        stream.write(chunk); digest.update(chunk)
                        chunk=response.read(1024*1024)
                record.update(status='downloaded', bytes=destination.stat().st_size, sha256=digest.hexdigest())
    except (HTTPError, URLError, TimeoutError) as error:
        record.update(status='access_failed_unresolved', error=str(error), http_status=getattr(error,'code',None))
    (META/'access'/f'{time.time_ns()}_{Path(name).name}.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
    print(json.dumps({k:record.get(k) for k in ['source_id','source_file','status','bytes','error']},ensure_ascii=False),flush=True)
    return destination if record['status']=='downloaded' else None

def bootstrap():
    csvpath=fetch('https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/sub-est2025.csv','population/sub-est2025.csv','S01','2020-2025; vintage 2025')
    rankpath=fetch('https://www2.census.gov/programs-surveys/popest/tables/2020-2025/cities/totals/SUB-IP-EST2025-ANNRNK.xlsx','population/SUB-IP-EST2025-ANNRNK.xlsx','S01','July 1 2025; vintage 2025')
    build_population()

def build_population():
    csvpath=RAW/'population/sub-est2025.csv'
    rankpath=RAW/'population/SUB-IP-EST2025-ANNRNK.xlsx'
    # The downloaded Census source contains CP1252 place names (e.g. byte F1).
    data=pd.read_csv(csvpath,dtype=str,encoding='cp1252')
    places=data[data.SUMLEV=='162'].copy()
    places['population_2025']=places.POPESTIMATE2025.astype(int)
    places=places.sort_values('population_2025',ascending=False).head(25)
    places['population_rank']=range(1,26)
    places['city_id']=places.STATE.str.zfill(2)+places.PLACE.str.zfill(5)
    places['city_name']=places.NAME
    places['state']=places.STNAME
    places['state_fips']=places.STATE.str.zfill(2)
    places['place_fips']=places.PLACE.str.zfill(5)
    places['source_url']='https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/sub-est2025.csv'
    places['geography_type']='Census incorporated place or published balance, SUMLEV 162'
    places['population_vintage']='2025'
    cols=['population_rank','city_id','city_name','state','state_fips','place_fips','population_2025','population_vintage','geography_type','source_url']
    places[cols].to_csv(PROJECT/'data/metadata/cities.csv',index=False)
    places.to_csv(EXTRACTED/'population_25cities_2020_2025.csv',index=False)
    print(places[cols[:7]].to_string(index=False),flush=True)
    print('Official ranking workbook preview:\n',pd.read_excel(rankpath,header=None).head(10).to_string(index=False),flush=True)

def build_geography():
    cities=pd.read_csv(PROJECT/'data/metadata/cities.csv',dtype=str)
    states=pd.read_csv(RAW/'geography/national_state2020.txt',sep='|',dtype=str)
    cities['state_abbr']=cities.state_fips.map(states.set_index('STATEFP').STATE)
    assert cities.state_abbr.notna().all()
    cities.to_csv(PROJECT/'data/metadata/cities.csv',index=False)
    data=pd.read_csv(RAW/'population/sub-est2025.csv',dtype=str,encoding='cp1252')
    data['city_id']=data.STATE+data.PLACE
    parts=data[(data.SUMLEV=='157') & data.city_id.isin(cities.city_id)].copy()
    parts['county_id']=parts.STATE+parts.COUNTY
    for year in range(2020,2026):
        column=f'city_part_population_{year}'
        parts[column]=pd.to_numeric(parts[f'POPESTIMATE{year}'])
        parts[f'city_population_share_{year}']=parts[column]/parts.groupby('city_id')[column].transform('sum')
    assert set(parts.city_id)==set(cities.city_id)
    total=parts.groupby('city_id').city_part_population_2025.sum()
    assert all(total.loc[x.city_id]==int(x.population_2025) for x in cities.itertuples())
    columns=['city_id','county_id']+[f'{prefix}_{y}' for y in range(2020,2026) for prefix in ['city_part_population','city_population_share']]
    parts=parts[columns].merge(cities[['city_id','city_name','state']],on='city_id')
    parts['source_url']='https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/cities/totals/sub-est2025.csv'
    parts['mapping_note']='City residents in each county, V2025 SUMLEV157; not proportion of county residents'
    parts.to_csv(PROJECT/'data/metadata/city_county_crosswalk.csv',index=False)
    official=pd.read_excel(RAW/'geography/list1_2023.xlsx',skiprows=2,dtype=str)
    official=official[official['FIPS State Code'].notna() & official['FIPS County Code'].notna()].copy()
    official['county_id']=official['FIPS State Code'].str.zfill(2)+official['FIPS County Code'].str.zfill(3)
    official['cbsa_id']=official['CBSA Code'].str.zfill(5)
    official[['county_id','cbsa_id','CBSA Title','County/County Equivalent','State Name']].to_csv(EXTRACTED/'county_cbsa_2023.csv',index=False)
    mapping=parts.merge(official[['county_id','cbsa_id','CBSA Title','County/County Equivalent']],on='county_id',how='left',validate='many_to_one')
    assert mapping.cbsa_id.notna().all()
    mapping['cbsa_delineation']='July 2023'
    mapping.to_csv(PROJECT/'data/metadata/city_county_cbsa_crosswalk.csv',index=False)
    print('County/CBSA mapping:',len(mapping),'pairs,',mapping.city_id.nunique(),'cities',flush=True)

def download_acs():
    annual=['B01001','B01003','B02001','B03003','B14001','B14003','B14005','B17001','B18101','B19013','B19113','B23001','B25031','B25064','B25070','B25074','B08201','B08301','B28002','B28005','C16001']
    small_area=['B01001','B14001','B17001','B19013','B25031','B25064','B25070','B08201','B28002']
    jobs=[]
    for year,yrs,tables in [(2024,1,annual),(2025,1,annual),(2024,5,small_area)]:
        index=(RAW/f'acs/{year}_{yrs}YR_index.html').read_text()
        links=re.findall(r'href=[\"\']([^\"\']+)',index)
        for table in tables:
            name=f'acsdt{yrs}y{year}-{table.lower()}.dat'
            assert name in links, (year,yrs,name)
            url=f'https://www2.census.gov/programs-surveys/acs/summary_file/{year}/table-based-SF/data/{yrs}YRData/{name}'
            jobs.append((url,f'acs/{year}_{yrs}YR/{name}','S02',f'{year-yrs+1}-{year}' if yrs>1 else str(year)))
    with ThreadPoolExecutor(max_workers=5) as pool:
        results=list(pool.map(lambda args:fetch(*args),jobs))
    print('ACS files downloaded:',sum(x is not None for x in results),'/',len(jobs),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='bootstrap': bootstrap()
    elif sys.argv[1]=='population': build_population()
    elif sys.argv[1]=='geography': build_geography()
    elif sys.argv[1]=='acs-download': download_acs()
