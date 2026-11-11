"""Extract official EDFacts archives, preserving censored intervals and data notes."""
import csv,zipfile,io,json,re,collections
from collect_education_inclusion import BASE,RAW,META
from collect_education_inclusion_extract import edge,write,OUT,CITIES,CITY,LONG_FIELDS
loc=edge('2021');leacities=collections.defaultdict(set)
for x in loc.values():leacities[x['leaid']].add(x['city_id'])
logs=[json.loads(x) for x in (META/'access_log.jsonl').read_text().splitlines()]
urls={x['local_path'].split('/')[-1]:x['url'] for x in logs if x.get('status')=='downloaded'}
long=[];coverage=[]
for file in sorted(RAW.glob('SY*_FS150_FS151_DG695_DG696_*_data_files.zip')):
 level=file.name.split('_')[-3];selected=[]
 with zipfile.ZipFile(file) as z:
  for name in z.namelist():
   if '_data_notes' in name or name.endswith('README.txt'):
    target=META/'edfacts_documentation'/name;target.parent.mkdir(exist_ok=True);target.write_bytes(z.read(name));continue
   reader=csv.DictReader(io.TextIOWrapper(z.open(name),encoding='utf-8-sig'))
   for r in reader:
    if level=='SCH':cids=[loc[r['NCES SCH ID']]['city_id']] if r['NCES SCH ID'] in loc else []
    elif level=='LEA':cids=sorted(leacities[r['NCES LEA ID']])
    else:cids=[c['city_id'] for c in CITIES if c['state'].upper()==r['State']]
    for cid in cids:
     selected.append(dict(city_id=cid,**r));c=CITY[cid]
     # Long table is all-student total; complete subgroup observations remain in wide output.
     if not r['Subgroup'].startswith('All Students'):continue
     raw=r['Value'];exact=re.fullmatch(r'(\d+(?:\.\d+)?)%',raw)
     low=high='';interval=re.fullmatch(r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)%',raw)
     if interval:low,high=interval.groups()
     if exact:low=high=exact.group(1)
     bound=re.fullmatch(r'([<>]=?)(\d+(?:\.\d+)?)%',raw)
     if bound:
      if bound.group(1).startswith('>'):low=bound.group(2)
      else:high=bound.group(2)
     indicators={'ACGR_exact_percent':exact.group(1) if exact else '', 'ACGR_lower_bound':low,'ACGR_upper_bound':high,'ACGR_cohort_count':r['Denominator'] if r['Denominator'].isdigit() else ''}
     note='Official EDFacts public use; censored interval/operator preserved: '+raw+'; COVID diploma requirements may differ; see source data notes. '
     if level=='SCH':geo='school point within Census ACS2025 place using 2020-21 NCES coordinates';gid=r['NCES SCH ID'];note+='School outcome, not city resident outcome.'
     elif level=='LEA':geo='LEA associated with school points in city';gid=r['NCES LEA ID'];note+='Whole-district outcome; district may span several places; not apportioned.'
     else:geo='state background only';gid=c['state_fips'];note+='Whole-state outcome; not city outcome.'
     for ind,val in indicators.items():long.append(dict(city_id=cid,city_name=c['city_name'],state=c['state'],source_id='S06',indicator_id=ind,value=val,unit='students' if ind.endswith('count') else 'percent',observation_period=r['School Year'],geography_type=geo,source_geo_id=gid,source_url=urls[file.name],quality_note=note,raw_value=r['Denominator'] if ind.endswith('count') else raw))
 write(OUT/file.name.replace('_data_files.zip','_25cities.csv'),selected)
 for c in CITIES:
  rs=[r for r in selected if r['city_id']==c['city_id'] and r['Subgroup'].startswith('All Students')]
  coverage.append(dict(city_id=c['city_id'],city_name=c['city_name'],source_file=file.name,level=level,all_student_records=len(rs),nonmissing_rate_or_interval=sum(r['Value'] not in ['S','.','','-'] for r in rs),exact_rates=sum(bool(re.fullmatch(r'\d+(?:\.\d+)?%',r['Value'])) for r in rs)))
write(OUT/'edfacts_official_indicators.csv',long,LONG_FIELDS)
write(META/'edfacts_official_city_coverage.csv',coverage)
print('Official EDFacts long rows',len(long),'coverage',len(coverage))
