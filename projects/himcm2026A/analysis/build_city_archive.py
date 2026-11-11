"""Package complete selected-city fields and provenance for bounded Git API uploads."""
from pathlib import Path
import base64, csv, hashlib, json, zipfile
from datetime import datetime, timezone

P=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    files=set()
    for folder in ['data/extracted','data/metadata','data/processed']:
        for p in (P/folder).rglob('*'):
            if not p.is_file():continue
            if any(s in p.name.lower() for s in ['seda','github_checkpoint_upload','city_data_archive','bundle_upload']):continue
            if p.suffix=='.log' or p.name in ['jacksonville_annual_report_2024.txt','jso_doc_59.txt']:continue
            if p.name.endswith('.gz') and p.with_suffix('').exists():continue
            files.add(p)
    # Keep complete source attributes for selected cities; country-wide source packages
    # stay in the download inventory rather than replicating unrelated US records.
    edu={r['path']:r['publication'] for r in csv.DictReader((P/'data/metadata/education_inclusion/raw_publication_inventory.csv').open())}
    for p in (P/'data/raw').rglob('*'):
        if not p.is_file() or p.name.endswith('.gz'):continue
        rel=str(p.relative_to(P));domain=p.relative_to(P/'data/raw').parts[0]
        if domain=='policy_parameters':
            if not p.name.startswith(('cdc_','dol_','nhts_')):continue
        if domain=='education_inclusion':
            if 'LOCAL' in edu.get(rel,'LOCAL'):continue
        if any(s in p.name.lower() for s in ['seda','hrc_2025','jacksonville_annual_report','fbi_main.js','fbi_2025_downloads','fbi_downloads_payload','search_evidence']):continue
        if p.suffix in ['.js','.html']:continue
        include=p.stat().st_size<=1_000_000
        if domain=='foundation' and p.parent.name=='population':include=True
        if domain=='foundation' and 'Table_Shells' in p.name:include=True
        if p.name=='census_acs2025_city_polygons.json':include=True
        if p.name.startswith('dryad_ntl_'):include=True
        if include:files.add(p)
    archive=P/'data/archives/collected_city_data.zip';archive.parent.mkdir(exist_ok=True)
    members=[]
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):
            rel=str(p.relative_to(P));z.write(p,rel)
            members.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
    # Verify each stored member equals its selected source.
    with zipfile.ZipFile(archive) as z:
        for row in members:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
    parts=[];directory=P/'data/archives/city_data_parts';directory.mkdir(exist_ok=True)
    with archive.open('rb') as f:
        i=0
        while raw:=f.read(128*1024):
            i+=1;content=base64.b64encode(raw)+b'\n';path=directory/f'part_{i:04d}.b64'
            path.write_bytes(content)
            gitsha=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
            parts.append(dict(path=str(path.relative_to(P)),bytes=len(content),raw_bytes=len(raw),sha256=sha(path),git_blob_sha=gitsha))
    manifest=dict(created_at=datetime.now(timezone.utc).isoformat(),cities=25,
        archive_path=str(archive.relative_to(P)),archive_bytes=archive.stat().st_size,archive_sha256=sha(archive),
        part_encoding='base64 ASCII with trailing LF; concatenate decoded part bytes in manifest order',
        members=members,parts=parts,scope='All selected-city extracted fields and related county reserve, provenance, permitted supporting source files. National bulk packages not included are explicitly inventoried; SEDA/HRC/TPL restricted originals excluded.')
    (P/'data/metadata/city_data_archive.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({k:manifest[k] for k in ['cities','archive_bytes','archive_sha256']})+f' members={len(members)} parts={len(parts)}',flush=True)

if __name__=='__main__':build()
