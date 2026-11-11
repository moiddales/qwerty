from collect_safety_health import *
changed=[]
for f in META.glob('*.access.json'):
 d=json.loads(f.read_text())
 for key in ['url','final_url']:
  if key in d:d[key]=redact_url(d[key])
 p=BASE/d['path']
 if p.exists():
  data=p.read_bytes();new=redact_payload(data,p.name)
  if data!=new:
   d['original_response_sha256']=d.get('original_response_sha256',hashlib.sha256(data).hexdigest());d['redaction']='Public embedded API key / expiring signed URL credentials redacted in stored discovery evidence'
   p.write_bytes(new);d['sha256']=hashlib.sha256(new).hexdigest();d['size_bytes']=len(new);changed.append(p.name)
 f.write_text(json.dumps(d,ensure_ascii=False,indent=2))
print('Sanitized discovery payloads:',len(changed))
