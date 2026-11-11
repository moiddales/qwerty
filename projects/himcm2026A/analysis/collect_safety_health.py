"""Download official safety/health source files, retaining evidence and SHA256.
Run from any directory. Failures are recorded as failures, never as zero data.
"""
import csv,datetime,hashlib,json,pathlib,urllib.request,urllib.error,urllib.parse,concurrent.futures,zipfile,re
BASE=pathlib.Path(__file__).resolve().parents[1]
RAW=BASE/'data/raw/safety_health'; META=BASE/'data/metadata/safety_health'; EXT=BASE/'data/extracted/safety_health'
for p in [RAW,META,EXT]:p.mkdir(parents=True,exist_ok=True)

def redact_url(url):
    parts=urllib.parse.urlsplit(url)
    sensitive={'api_key','apikey','awsaccesskeyid','signature','x-amz-credential','x-amz-signature','x-amz-security-token'}
    query=[(k,'REDACTED' if k.lower() in sensitive else v) for k,v in urllib.parse.parse_qsl(parts.query,keep_blank_values=True)]
    return urllib.parse.urlunsplit((parts.scheme,parts.netloc,parts.path,urllib.parse.urlencode(query),parts.fragment))
def redact_payload(data,name):
    if name.endswith('.js'):
        return re.sub(rb'API_KEY=[A-Za-z0-9]+',b'API_KEY=REDACTED',data)
    if name.startswith('fbi_signed') and name.endswith('.json'):
        obj=json.loads(data)
        return json.dumps({k:redact_url(v) if isinstance(v,str) else v for k,v in obj.items()}).encode()
    return data

def fetch(item):
    sid,url,name,geo,version=item
    path=RAW/name
    rec=dict(source_id=sid,url=redact_url(url),retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_version=version,geography=geo,license='US federal government source; public data; source attribution retained',path=str(path.relative_to(BASE)))
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research data collection)'})
        with urllib.request.urlopen(req,timeout=90) as r:
            data=r.read();rec.update(status=r.status,content_type=r.headers.get('Content-Type'),final_url=redact_url(r.url))
        original_sha256=hashlib.sha256(data).hexdigest();sanitized=redact_payload(data,name)
        if sanitized!=data:rec.update(redaction='Public embedded API key / expiring signed-URL credential redacted; no key used by data collection',original_response_sha256=original_sha256)
        data=sanitized
        path.write_bytes(data);rec.update(success=True,size_bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        if name.endswith('.zip'):
            with zipfile.ZipFile(path) as z:rec['archive_members']=z.namelist()
        print(name,rec['status'],len(data),flush=True)
    except Exception as e:
        rec.update(success=False,error=str(e),status=getattr(e,'code',None));print(name,'FAILED',str(e),flush=True)
    (META/(name.replace('/','_')+'.access.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2))
    return rec
if __name__=='__main__':
    items=[]
    for year in range(2021,2026):
        for geo in ['county','cbsa']:
            n=f'annual_aqi_by_{geo}_{year}.zip';items.append(('S10','https://aqs.epa.gov/aqsweb/airdata/'+n,n,geo,str(year)))
    items += [
      ('S10','https://aqs.epa.gov/aqsweb/airdata/annual_conc_by_monitor_2025.zip','annual_conc_by_monitor_2025.zip','monitor','2025'),
      ('S10','https://aqs.epa.gov/aqsweb/airdata/download_files.html','epa_download_documentation.html','documentation','live'),
      ('S13','https://data.hrsa.gov/DataDownload/DD_Files/BCD_HPSA_FCT_DET_MH.csv','hrsa_mental_health_hpsa.csv','designation','live snapshot'),
      ('S12','https://www.cdc.gov/yrbs/data/index.html','yrbs_data.html','documentation','live'),
      ('S12','https://www.cdc.gov/yrbs/results/index.html','yrbs_results.html','documentation','live'),
      ('S14','https://www.samhsa.gov/data/report/2025-national-directory-mental-health-treatment-facilit','samhsa_directory.html','facility','2025'),
      ('S15','https://data.cdc.gov/api/views/vgc8-iyc4/columns.json','places_columns.json','place','2025'),
      ('S08','https://cde.ucr.cjis.gov/','fbi_cde.html','agency','live'),
      ('S09','https://cdan.dot.gov/stsi/stsi.htm','fars_stsi.html','state/county/city','live'),
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:list(ex.map(fetch,items))
