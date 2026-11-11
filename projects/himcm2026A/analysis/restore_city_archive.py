"""Reconstruct and verify the complete 25-city data archive from Git text parts."""
from pathlib import Path
import argparse, base64, hashlib, json, zipfile

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--extract',action='store_true');args=parser.parse_args()
    project=Path(__file__).resolve().parents[1]
    m=json.loads((project/'data/metadata/city_data_archive.json').read_text())
    archive=project/m['archive_path']
    with archive.open('wb') as out:
        for part in m['parts']:
            content=(project/part['path']).read_bytes()
            assert hashlib.sha256(content).hexdigest()==part['sha256'],part['path']
            decoded=base64.b64decode(content);assert len(decoded)==part['raw_bytes']
            out.write(decoded)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==m['archive_sha256']
    with zipfile.ZipFile(archive) as z:
        for member in m['members']:
            data=z.read(member['path']);assert hashlib.sha256(data).hexdigest()==member['sha256'],member['path']
            if args.extract:
                target=(project/member['path']).resolve()
                assert target.is_relative_to(project.resolve()),'Unexpected archive path'
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print(f'Verified {len(m["members"])} files for {m["cities"]} cities: {archive}')
    if not args.extract:print('Use --extract to restore source-relative file paths.')

if __name__=='__main__':main()
