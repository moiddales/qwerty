"""Download official education/inclusion sources with explicit access evidence."""
import csv, hashlib, json, pathlib, urllib.request, urllib.error, datetime, sys
BASE=pathlib.Path(__file__).resolve().parents[1]
RAW=BASE/'data/raw/education_inclusion'; META=BASE/'data/metadata/education_inclusion'
RAW.mkdir(parents=True,exist_ok=True); META.mkdir(parents=True,exist_ok=True)
def fetch(url,name,source,year='',geography='',license='US federal government public data'):
    path=RAW/name
    record=dict(source_id=source,url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),observation_period=year,geography=geography,license=license,local_path=str(path.relative_to(BASE)))
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research data collection)'})
        with urllib.request.urlopen(req,timeout=90) as r, path.open('wb') as f:
            record.update(http_status=r.status,content_type=r.headers.get('Content-Type'),final_url=r.url)
            digest=hashlib.sha256()
            while chunk:=r.read(1024*1024):
                f.write(chunk); digest.update(chunk)
        record.update(status='downloaded' if path.stat().st_size else 'empty_response',bytes=path.stat().st_size,sha256=digest.hexdigest())
        if not path.stat().st_size:record['error']='Empty HTTP response; not a dataset'
    except Exception as e:
        record.update(status='failed',error=str(e),http_status=getattr(e,'code',None))
        if path.exists(): path.unlink()
    with (META/'access_log.jsonl').open('a') as f: f.write(json.dumps(record)+'\n')
    print(json.dumps(record),flush=True)
    return path if record['status']=='downloaded' else None
if __name__=='__main__':
    if sys.argv[1:] == ['--replay']:
        # Only actual successful downloads; deterministic distinct source URL and filename.
        records=[json.loads(x) for x in (META/'access_log.jsonl').read_text().splitlines()]
        seen=set()
        for r in records:
            name=pathlib.Path(r['local_path']).name
            if r.get('status')!='downloaded' or (r['url'],name) in seen:continue
            seen.add((r['url'],name))
            if (RAW/name).exists():continue
            fetch(r['url'],name,r['source_id'],r['observation_period'],r['geography'],r['license'])
    else:fetch(*sys.argv[1:])
