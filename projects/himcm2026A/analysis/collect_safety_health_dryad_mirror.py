"""Independent S27 check using official NTL mirror; no authenticated access attempted."""
import pathlib,urllib.request,urllib.error,datetime,hashlib,json,concurrent.futures,zipfile,csv,io
BASE=pathlib.Path(__file__).resolve().parents[1];RAW=BASE/'data/raw/mobility_opportunities';META=BASE/'data/metadata/mobility_opportunities'
def get(item):
 name,url=item;rec=dict(source_id='S27',url=url,retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),license='CC0-1.0 per Dryad/NTL record',source_geography='Santa Cruz County survey, not 25-city indicators',source_version='2025-08-25 dataset publication',path=str((RAW/name).relative_to(BASE)))
 try:
  with urllib.request.urlopen(url,timeout=60) as r:b=r.read();rec.update(status=r.status,content_type=r.headers.get('Content-Type'),final_url=r.url)
  (RAW/name).write_bytes(b);rec.update(success=True,size_bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 except urllib.error.HTTPError as e:
  b=e.read();rec.update(success=False,status=e.code,content_type=e.headers.get('Content-Type'),error=str(e),error_body_excerpt=b[:1500].decode(errors='replace'))
 except Exception as e:rec.update(success=False,error=str(e))
 (META/(name+'.request.json')).write_text(json.dumps(rec,ensure_ascii=False,indent=2));print(name,rec.get('status'),rec['success'],flush=True)
 return rec
items=[('dryad_ntl_mirror.zip','https://rosap.ntl.bts.gov/view/dot/86232/dot_86232_DS1.zip'),('dryad_ntl_record.html','https://rosap.ntl.bts.gov/view/dot/86232'),('dryad_api_auth_documentation.md','https://raw.githubusercontent.com/datadryad/dryad-app/main/documentation/apis/api_accounts.md'),('dryad_ucdavis_record.html','https://ncst.ucdavis.edu/research-product/dataset-fare-free-transit-youth-exploring-transit-use-and-behavior-change')]
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:list(ex.map(get,items))
 if (RAW/'dryad_ntl_mirror.zip').exists():
  import openpyxl
  official=json.loads((RAW/'dryad_files.json').read_text())['_embedded']['stash:files']
  expected={r['path']:r for r in official};verification=[]
  with zipfile.ZipFile(RAW/'dryad_ntl_mirror.zip') as z:
   for name in z.namelist():
    b=z.read(name);dest=RAW/('dryad_ntl_'+pathlib.Path(name).name)
    dest.write_bytes(b)
    sha=hashlib.sha256(b).hexdigest();entry=dict(member=name,path=str(dest.relative_to(BASE)),size_bytes=len(b),sha256=sha,dryad_sha256_match=sha==expected[name]['digest'] if name in expected else None)
    if name.endswith('.csv'):
     rows=list(csv.reader(io.StringIO(b.decode('utf-8-sig'))));entry.update(data_rows=len(rows)-1,columns=len(rows[0]),row_widths=sorted(set(map(len,rows))),column_names=rows[0],readme_claim='392 rows and 127 variables',dimension_note='Actual downloaded CSV has392 data rows and129 columns; all records width129; Dryad SHA256 matches exactly')
    if name.endswith('.xlsx'):
     wb=openpyxl.load_workbook(io.BytesIO(b),read_only=True,data_only=True);entry['sheets']=[dict(name=s.title,rows=s.max_row,columns=s.max_column) for s in wb]
    verification.append(entry)
  record=dict(source_id='S27',doi='10.5061/dryad.612jm64fn',mirror_record='https://rosap.ntl.bts.gov/view/dot/86232',mirror_url=items[0][1],license='CC0-1.0',retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),geography='Santa Cruz County high school survey, collected2024; independent extension, zero target-city direct coverage',files=verification,api_401_classification='Dryad official API accounts documentation states downloading files requires token for any call; no token requested or used',web_403_classification='Cause unverified; no inference about physical computer access')
  (META/'dryad_ntl_mirror_verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
  print(json.dumps({r['member']: {k:v for k,v in r.items() if k in ['data_rows','columns','dryad_sha256_match','sheets']} for r in verification},ensure_ascii=False))
