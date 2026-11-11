"""Lossless gzip preserves large original statistical text files for Git storage."""
from collect_foundation import *
import gzip, shutil

def checksum(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''): digest.update(block)
    return digest.hexdigest()

def archive(path):
    target=path
    if path.stat().st_size>1_000_000 and path.suffix.lower() in ('.dat','.csv','.txt','.json','.geojson'):
        target=path.with_name(path.name+'.gz')
        with path.open('rb') as f,target.open('wb') as stream:
            with gzip.GzipFile(fileobj=stream,mode='wb',mtime=0) as gz: shutil.copyfileobj(f,gz,2**20)
        digest=hashlib.sha256()
        with gzip.open(target,'rb') as f:
            for block in iter(lambda:f.read(2**20),b''):digest.update(block)
        assert digest.hexdigest()==checksum(path)
    return dict(source_path=str(path.relative_to(PROJECT)),archive_path=str(target.relative_to(PROJECT)),
                source_bytes=path.stat().st_size,archive_bytes=target.stat().st_size,
                source_sha256=checksum(path),archive_sha256=checksum(target),compression='gzip' if target!=path else 'none')

if __name__=='__main__':
    files=[p for p in RAW.rglob('*') if p.is_file() and p.suffix!='.gz']
    with ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(archive,files))
    pd.DataFrame(rows).to_csv(META/'archive_manifest.csv',index=False)
    print('Foundation archived',len(rows),'files',sum(r['archive_bytes'] for r in rows),'bytes',flush=True)
