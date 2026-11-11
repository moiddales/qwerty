"""Download evidenced official source URLs; retain request outcomes and hashes."""
import argparse, concurrent.futures, datetime, hashlib, json, pathlib, urllib.request, urllib.error, urllib.parse
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/mobility_opportunities'
META=ROOT/'data/metadata/mobility_opportunities'
def fetch(item):
    url,name,source,version,geography,license_note=item[:6]
    post=urllib.parse.urlencode(item[6]).encode() if len(item)>6 else None
    p=RAW/name
    partial=RAW/(name+".part")
    record=dict(method='POST' if post else 'GET',request_parameters=item[6] if post else None,url=url,path=str(p.relative_to(ROOT)),source_id=source,version=version,geography=geography,license=license_note,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        with urllib.request.urlopen(urllib.request.Request(url,data=post,headers={'User-Agent':'HiMCM academic data collection; Python urllib'}),timeout=120) as r:
            record.update(status=r.status,content_type=r.headers.get('Content-Type'),last_modified=r.headers.get('Last-Modified'),final_url=r.url)
            with partial.open('wb') as f:
                while chunk:=r.read(1024*1024):f.write(chunk)
        partial.replace(p)
        record.update(size=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),outcome='downloaded')
    except Exception as e:
        record.update(status=getattr(e,'code',None),outcome='failed',failure_reason=str(e))
        if partial.exists():partial.unlink()
    (META/(name+'.'+hashlib.sha256(url.encode()).hexdigest()[:10]+'.request.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False),flush=True)
    return record
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('manifest');args=a.parse_args()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(fetch,json.loads(pathlib.Path(args.manifest).read_text())))
