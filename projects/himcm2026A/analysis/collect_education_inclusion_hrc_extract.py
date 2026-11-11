import csv,json,re,pdfplumber
from collect_education_inclusion import BASE,RAW,META
OUT=BASE/'data/extracted/education_inclusion'
cities=list(csv.DictReader((BASE/'data/metadata/cities.csv').open()))
logs=[json.loads(s) for s in (META/'access_log.jsonl').read_text().splitlines()]
urls={x['local_path'].split('/')[-1]:x['url'] for x in logs if x.get('status')=='downloaded'}
rows=[]
fields=['city_id','city_name','state','source_id','indicator_id','value','unit','observation_period','geography_type','source_geo_id','source_url','quality_note']
for c in cities:
 f=RAW/f"hrc_2025_{c['city_id']}.pdf"
 if not f.exists():
  rows.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id='S23',indicator_id='MEI_final_score',value='',unit='points',observation_period='2025',geography_type='municipality',source_geo_id=c['city_id'],source_url='https://www.hrc.org/resources/municipal-equality-index',quality_note='Washington DC not covered in MEI city scorecard universe; no replacement score imputed'))
  continue
 with pdfplumber.open(f) as d:
  p=d.pages[0]; left=p.crop((0,p.bbox[1],421,p.bbox[3])).extract_text(); right=p.crop((421,p.bbox[1],p.width,p.bbox[3])).extract_text()
 # Local PDF remains the evidence; only factual numeric observations are published.
 vals={}
 for code,txt,maximum in [('nondiscrimination',left,30),('municipal_employer',left,28),('municipal_services',left,12),('law_enforcement',right,22),('leadership',right,8)]:
  m=re.search(r'SCORE\s+(\d+)\s+out of\s+'+str(maximum)+r'\b',txt);assert m,(c['city_name'],code);vals['MEI_'+code+'_score']=m.group(1)
 m=re.search(r'Final Score\s+(\d+)',right);assert m,c['city_name'];vals['MEI_final_score']=m.group(1)
 for term,code in [('Human Rights Commission','human_rights_commission'),('NDO Enforcement by Commission','ndo_commission_enforcement'),('LGBTQ\\+ Liaison to City Executive','executive_lgbtq_liaison')]:
  m=re.search(term+r'\s+([0-9 ]+)\n',left);assert m,(c['city_name'],code)
  nums=m.group(1).split();vals['MEI_'+code+'_municipal_points']=nums[-2]
 m=re.search(r'Protects Youth from\s+([0-9 +]+)\n',left);assert m,c['city_name'];ns=m.group(1).split();vals['MEI_conversion_therapy_municipal_points']=ns[-2]
 m=re.search(r'Youth Bullying Prevention Policy for\s+([0-9 +]+)\n',left);assert m,c['city_name'];ns=re.findall(r'\d',m.group(1).split('+')[0]);assert len(ns)==2,(c['city_name'],ns);vals['MEI_youth_bullying_SO_points']=ns[0];vals['MEI_youth_bullying_GI_points']=ns[1]
 m=re.search(r'City Provides Services to LGBTQ\+\s+(\d+)\s+\+2\nYouth',left);assert m,c['city_name'];vals['MEI_lgbtq_youth_services_points']=m.group(1)
 for k,v in vals.items():rows.append(dict(city_id=c['city_id'],city_name=c['city_name'],state=c['state'],source_id='S23',indicator_id=k,value=v,unit='points',observation_period='2025',geography_type='municipality',source_geo_id=c['city_id'],source_url=urls[f.name],quality_note='HRC scorecard numeric fact; awarded points reflect MEI definitions, not youth lived experience. Nashville/Indianapolis jurisdiction may differ from Census balance; original scorecard retained locally.'))
with (OUT/'hrc_2025_city_policy_indicators.csv').open('w',newline='') as h:
 w=csv.DictWriter(h,fields);w.writeheader();w.writerows(rows)
print('HRC rows',len(rows),'cities',len({r['city_id'] for r in rows}))
