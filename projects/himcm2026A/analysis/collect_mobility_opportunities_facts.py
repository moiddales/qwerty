"""Record access evidence and limited numeric citations without republishing TPL materials."""
import urllib.request,datetime,hashlib,json,concurrent.futures
from collect_mobility_opportunities import META
items=[('columbus-ohio',71),('indianapolis-city-balance-indiana',36),('las-vegas-nevada',70)]
def read(item):
 slug,value=item;url='https://www.tpl.org/city/'+slug
 rec=dict(url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),version='dynamic webpage; measurement vintage not confirmed',license='TPL general terms restrict redistribution; only numerical fact cited, no original retained',geography='named city/Census balance')
 try:
  with urllib.request.urlopen(url,timeout=60) as r:b=r.read();rec.update(status=r.status,content_type=r.headers.get('Content-Type'),size=len(b),sha256=hashlib.sha256(b).hexdigest(),quoted_numeric_fact_percent=value,original_archived=False)
 except Exception as e:rec.update(status=getattr(e,'code',None),failure_reason=str(e),web_search_channel_verified_fact=value)
 (META/f'tpl_{slug}_fact_evidence.json').write_text(json.dumps(rec,indent=2)+'\n');print(slug,rec.get('status'))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(read,items))
