"""Fetch official wage evidence; retain originals locally, publish access facts only.

Run from any directory: python projects/himcm2026A/analysis/collect_youth_wages.py
Optional source IDs select a small batch. No account, paid request, or external write.
"""
import concurrent.futures
import datetime
import html
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'supplement_20261111/wages'
RAW = ROOT / 'raw_local'


def fetch(source):
    sid, url = source['source_id'], source['url']
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    row = dict(source_id=sid, requested_url=url, requested_at_utc=started,
               channel='local Python urllib GET on user Windows computer',
               permission='ordinary read-only public HTTP request authorized',
               license_stage='public official source; facts and URLs published; original redistribution not asserted')
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=25) as response:
            body = response.read()
            row.update(http_status=response.status, final_url=response.url,
                       content_type=response.headers.get('Content-Type', ''))
    except urllib.error.HTTPError as exc:
        body = exc.read()
        row.update(http_status=exc.code, final_url=exc.url,
                   content_type=exc.headers.get('Content-Type', ''), error=str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        row.update(http_status='', final_url='', content_type='', bytes=0,
                   fetch_stage='transport_failed', parse_stage='not_attempted', error=str(exc),
                   raw_local_path='', parsed_local_path='', expected_terms_found='')
        return row
    suffix = '.pdf' if body.startswith(b'%PDF-') else '.html'
    original = RAW / (sid + suffix)
    original.write_bytes(body)
    row.update(bytes=len(body), raw_local_path=str(original.relative_to(BASE)))
    if suffix == '.pdf':
        import pymupdf
        with pymupdf.open(stream=body, filetype='pdf') as document:
            parsed = '\n'.join(page.get_text() for page in document)
        row['parse_stage'] = 'pdf_text_extracted' if parsed.strip() else 'pdf_no_extractable_text'
    else:
        parsed = body.decode('utf-8', errors='replace')
        parsed = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', parsed, flags=re.I | re.S)
        parsed = html.unescape(re.sub(r'<[^>]+>', ' ', parsed))
        parsed = re.sub(r'\s+', ' ', parsed).strip()
        row['parse_stage'] = 'html_text_extracted'
    text_file = RAW / (sid + '.txt')
    text_file.write_text(parsed, encoding='utf-8')
    row['parsed_local_path'] = str(text_file.relative_to(BASE))
    terms = source.get('expected_terms', [])
    found = [term for term in terms if term.lower() in parsed.lower()]
    row['expected_terms_found'] = '|'.join(found)
    if row['http_status'] != 200:
        row['fetch_stage'] = 'http_error_body_saved'
    elif 'request rejected' in parsed.lower() or 'access denied' in parsed[:1000].lower():
        row['fetch_stage'] = 'http_200_rejection_page'
    elif terms and not found:
        row['fetch_stage'] = 'downloaded_expected_content_not_confirmed'
    else:
        row['fetch_stage'] = 'downloaded_content_confirmed'
    return row


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))
    selected = [s for s in catalog if not sys.argv[1:] or s['source_id'] in sys.argv[1:]]
    log_path = ROOT / 'access_log.jsonl'
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch, selected):
            with log_path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(result, ensure_ascii=False) + '\n')
            print(json.dumps({key: result.get(key, '') for key in
                              ('source_id', 'http_status', 'fetch_stage', 'bytes')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
