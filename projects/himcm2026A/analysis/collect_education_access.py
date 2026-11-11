"""Fetch official education access evidence and publish traceable short policy facts.

Run from any directory.  The manually coded catalogue is the research input;
full HTML/PDF responses stay in ignored raw_local, not in the publication.
"""
import argparse
import concurrent.futures
import csv
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'supplement_20261111/education_access'
RAW = OUT / 'raw_local'


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.skip += 1
        elif tag in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'br', 'tr'):
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def normalized(s):
    return re.sub(r'\s+', ' ', unescape(s)).strip().casefold()


def extract_html(html):
    parser = PageText()
    parser.feed(html)
    # Apptegy/Thrillshare embeds the actual page's content as JSON HTML blocks.
    # Reading these blocks avoids treating an empty server-rendered shell as data.
    def page_blocks(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'html' and isinstance(item, str):
                    parser.feed(item)
                else:
                    page_blocks(item)
        elif isinstance(value, list):
            for item in value:
                page_blocks(item)
    for match in re.finditer(r'window\.clientWorkStateTemp\s*=\s*JSON\.parse\(("(?:[^"\\]|\\.)*")\)', html):
        page_blocks(json.loads(json.loads(match.group(1))))
    return re.sub(r'[ \t\r\f\v]+', ' ', ''.join(parser.parts))


def extract_document(path):
    if path.suffix == '.pdf':
        import fitz
        with fitz.open(path) as pdf:
            return '\n'.join(f'## PDF page {i+1}\n{page.get_text()}' for i,page in enumerate(pdf))
    return extract_html(path.read_text(encoding='utf-8', errors='replace'))


def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fetch(source):
    key = source['source_key']
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    result = dict(source_key=key, requested_url=source['url'], accessed_at_utc=stamp,
                  environment='user Windows local computer; curl.exe HTTPS GET',
                  method='GET', status_code='', content_type='', final_url='', bytes=0,
                  sha256='', valid_document=False, error='', local_response='', local_text='')
    response_path = RAW / (key + '.response')
    request = subprocess.run(['curl.exe', '-sS', '-L', '--max-time', '35', '-A', 'Mozilla/5.0 education-policy research',
                              '-o', str(response_path), '-w', '%{json}', source['url']], capture_output=True, text=True, encoding='utf-8', errors='replace')
    response_meta = json.loads(request.stdout)
    result.update(status_code=response_meta['response_code'],content_type=response_meta['content_type'] or '',
                  final_url=response_meta['url_effective'], error=request.stderr.strip())
    if not response_path.exists():
        return result
    body = response_path.read_bytes()
    response_path.unlink()
    suffix = '.pdf' if body.startswith(b'%PDF') else '.html'
    path = RAW / (key + suffix)
    path.write_bytes(body)
    result.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), local_response=path.relative_to(BASE).as_posix())
    page_text = extract_document(path)
    text_path = RAW / (key + '.txt')
    text_path.write_text(page_text, encoding='utf-8')
    result['local_text'] = text_path.relative_to(BASE).as_posix()
    result['valid_document'] = result['status_code'] == 200 and all(normalized(anchor) in normalized(page_text) for anchor in source['document_anchors'])
    return result


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--fetch', action='store_true', help='Fetch sources missing from access log; no retries.')
    args.add_argument('--source', action='append', help='Fetch only listed source keys.')
    opt = args.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(exist_ok=True)
    sources = json.loads((OUT / 'education_access_catalog.json').read_text(encoding='utf-8'))
    cities = {c['city_id']: c for c in csv.DictReader((BASE / 'data/metadata/cities.csv').open(encoding='utf-8'))}
    log_path = OUT / 'education_access_http_log.jsonl'
    logs = [json.loads(line) for line in log_path.read_text(encoding='utf-8').splitlines()] if log_path.exists() else []
    seen = {r['source_key'] for r in logs}
    if opt.fetch:
        todo = [s for s in sources if (s['source_key'] in opt.source if opt.source else s['source_key'] not in seen)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for result in pool.map(fetch, todo):
                with log_path.open('a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')
                logs.append(result)
                print(result['source_key'], result['status_code'], result['valid_document'], result['bytes'], flush=True)
    latest = {r['source_key']: r for r in logs}
    facts, registry, checks = [], [], []
    for source in sources:
        key = source['source_key']
        access = latest.get(key, {})
        text_path = access.get('local_text')
        page_text = ''
        if text_path:
            page_text = extract_document(BASE / access['local_response'])
            (BASE / text_path).write_text(page_text, encoding='utf-8')
        valid = access.get('status_code') == 200 and bool(text_path) and all(normalized(a) in normalized(page_text) for a in source['document_anchors'])
        registry.append(dict(source_key=key, city_ids=';'.join(source['city_ids']), district_or_provider=source['scope'],
                             title=source['title'], source_url=source['url'], school_year=source['period'],
                             retrieval_status='valid_document' if valid else 'access_or_document_pending',
                             licence='No blanket republication licence established; publish original short factual paraphrases and citations; full response excluded in raw_local.',
                             **{k: access.get(k, '') for k in ('accessed_at_utc', 'status_code', 'content_type', 'bytes', 'sha256', 'final_url')}))
        for index, fact in enumerate(source['facts'], 1):
            anchor_ok = normalized(fact['anchor']) in normalized(page_text) if text_path else False
            accepted = valid and anchor_ok
            checks.append(dict(source_key=key, fact_index=index, document_valid=valid, anchor_present=anchor_ok,
                               publication_status='accepted' if accepted else 'pending_verification', anchor=fact['anchor']))
            if not accepted:
                continue
            for cid in source['city_ids']:
                city = cities[cid]
                facts.append(dict(record_id=f'{key}_{index:02d}_{cid}', city_id=cid, city_name=city['city_name'],
                                  state=city['state_abbr'], source_id='S28', source_key=key,
                                  indicator_id='education_access_' + fact['topic'], value='', unit='policy_rule',
                                  value_text=fact['rule'], observation_period=source['period'],
                                  geography_type='district/provider policy scope; city association only',
                                  source_geo_id=source['scope'], program=fact.get('program', 'district enrollment'),
                                  grade_group=fact.get('grades', 'high school; see rule'), source_url=source['url'],
                                  source_section=fact.get('section', source['title']),
                                  quality_note=fact.get('note', '') + ' | Scope: ' + source['scope'] + '; other districts/campuses serving this city remain outside this source. Undated current rules are not retroactively assigned to a school year.',
                                  raw_value=fact['anchor'], accessed_at_utc=access['accessed_at_utc'],
                                  evidence_local_path=access['local_text'], evidence_status='local_HTTP_document_and_anchor_verified'))
    fact_fields = ['record_id','city_id','city_name','state','source_id','source_key','indicator_id','value','unit','value_text','observation_period','geography_type','source_geo_id','program','grade_group','source_url','source_section','quality_note','raw_value','accessed_at_utc','evidence_local_path','evidence_status']
    write_csv('education_access_facts.csv', facts, fact_fields)
    write_csv('education_access_sources.csv', registry, ['source_key','city_ids','district_or_provider','title','source_url','school_year','retrieval_status','licence','accessed_at_utc','status_code','content_type','bytes','sha256','final_url'])
    write_csv('education_access_fact_validation.csv', checks, ['source_key','fact_index','document_valid','anchor_present','publication_status','anchor'])
    topics = {
        'residency': 'Verify official resident enrollment eligibility, proof requirements and grade/age conditions for each resident-serving district.',
        'boundary_assignment': 'Obtain the school-year-specific official address-lookup rule or boundary file; connect resident addresses to eligible campuses.',
        'choice_selection': 'Verify program-specific tests, auditions, lotteries, priority groups and continuing-student rules.',
        'application_dates': 'Capture the relevant school year, opening/closing dates, deadlines and acceptance dates for each program.',
        'school_capacity': 'Obtain public school/grade seat, waiting-list or enrollment-capacity evidence; school capacity is separate from course capacity.',
        'dual_eligibility': 'Verify grade, GPA, placement scores, course prerequisites and school/guardian approval for each dual-credit provider.',
        'dual_cost': 'Verify tuition, textbooks, materials, registration/exam fees and aid eligibility for each dual-credit pathway.',
        'dual_schedule': 'Capture term dates, in-school/off-campus timing, travel and high-school schedule approval for dual-credit courses.',
        'dual_capacity': 'Find course-section seat limits, public enrollment or waiting-list rules; retain unknown available seats.',
        'ap_eligibility': 'Read campus course catalogue for AP prerequisites, minimum grades, grade level and permission; distinguish exam eligibility.',
        'ap_exam_eligibility': 'Verify AP examination eligibility and hosting-campus restrictions separately from AP course enrollment.',
        'ap_cost': 'Verify the current AP exam fee, district payment and fee-reduction eligibility at the relevant campus.',
        'ap_schedule': 'Obtain AP course-request deadlines, school timetable and conflict-resolution rules.',
        'ap_capacity': 'Obtain public AP section/seat or waitlist rules rather than treating course offering as individual access.',
        'ib_eligibility': 'Verify campus IB entry/continuation rules, grade level, academic prerequisites and diploma/course pathways.',
        'ib_cost': 'Verify current IB examination and participation fees and waiver/subsidy conditions.',
        'ib_schedule': 'Obtain IB course sequence, cohort timing and timetable restrictions.',
        'ib_capacity': 'Find public IB cohort/course seat limits or waitlist rules; retain unknown capacity.'
    }
    coverage = []
    for cid, city in cities.items():
        for topic in topics:
            selected = [r for r in facts if r['city_id'] == cid and r['indicator_id'] == 'education_access_' + topic]
            coverage.append(dict(city_id=cid,city_name=city['city_name'],topic=topic,
                                 evidence_rows=len(selected),status='partial_scope_facts_verified' if selected else 'not_yet_verified',
                                 source_keys=';'.join(sorted({r['source_key'] for r in selected})),
                                 missing_code='' if selected else 'UNVERIFIED',
                                 next_action=topics[topic],
                                 note='Verified rows cover the named district/provider/program only; expand to other resident-serving districts and campuses.'))
    write_csv('education_access_coverage.csv', coverage, ['city_id','city_name','topic','evidence_rows','status','source_keys','missing_code','next_action','note'])
    dictionary = [dict(field=key,definition=value) for key,value in {
        'record_id':'Unique source-key, fact index and city association. Not a student or school identifier.',
        'city_id':'Seven-character Census place/balance GEOID from the frozen cities.csv; preserve leading zeroes.',
        'city_name':'Frozen Census incorporated-place or published balance name.',
        'state':'Two-letter state abbreviation.',
        'source_id':'S28: official local/state/district supplements under the project source catalogue.',
        'source_key':'Join to education_access_sources.csv and acquisition attempts in education_access_http_log.jsonl.',
        'indicator_id':'education_access_ plus topic; topic is a policy construct, not a numeric city performance score.',
        'value':'Empty for qualitative policy facts. Never encode unknown eligibility/capacity as numeric zero.',
        'unit':'policy_rule for qualitative facts.',
        'value_text':'Original factual paraphrase coded from the cited official policy; preserve its stated conditions.',
        'observation_period':'Explicit school/application year when stated, otherwise current undated webpage or board policy.',
        'geography_type':'Named district/provider scope associated with a city; not citywide resident eligibility.',
        'source_geo_id':'Readable district/provider scope. Not a FIPS code and not a completed GIS boundary.',
        'program':'Program/pathway to which the rule applies; examination eligibility and course enrollment are distinct.',
        'grade_group':'School grade/age applicability when stated; otherwise see the detailed rule.',
        'source_url':'Official source URL; acquisition log preserves requested and final redirect URLs.',
        'source_section':'Section or title supporting manual coding.',
        'quality_note':'Observed scope, source-date conflict or other specific limitation.',
        'raw_value':'Short literal locator/anchor from the source; full original response is held locally in ignored raw_local.',
        'accessed_at_utc':'Actual local-machine HTTPS GET start time with UTC offset.',
        'evidence_local_path':'Project-relative local extracted text path; excluded from public Git files.',
        'evidence_status':'Local HTTP status, valid-document anchors and fact-anchor presence checked.',
        'UNVERIFIED':'No accepted policy fact in this topic/city cell yet; not evidence of zero access or unavailable data.'
    }.items()]
    write_csv('education_access_dictionary.csv', dictionary, ['field','definition'])
    directory = BASE / 'data/extracted/education_inclusion/ccd_2425/ccd_sch_029_2425_w_1a_073025.csv'
    lea_groups = {}
    for school in csv.DictReader(directory.open(encoding='utf-8-sig')):
        key = (school['city_id'], school['LEAID'])
        group = lea_groups.setdefault(key, dict(city_id=key[0],city_name=cities[key[0]]['city_name'],leaid=key[1],lea_name=school['LEA_NAME'],physical_high_schools=0,sample_school=school['SCH_NAME'],sample_school_website=school['WEBSITE'],status='resident_eligibility_not_yet_mapped_to_this_LEA',
                                              queue_basis='2024-25 operating schools with any grade9-12 located inside ACS2025 city polygon; school location does not establish resident-serving LEA coverage'))
        group['physical_high_schools'] += 1
    write_csv('education_access_lea_research_queue.csv', sorted(lea_groups.values(),key=lambda r:(r['city_id'],r['leaid'])), ['city_id','city_name','leaid','lea_name','physical_high_schools','sample_school','sample_school_website','status','queue_basis'])
    summary = dict(updated_at_utc=datetime.now(timezone.utc).isoformat(timespec='seconds'), cities_with_facts=len({r['city_id'] for r in facts}),
                   catalogue_sources=len(sources), valid_local_documents=sum(s['retrieval_status']=='valid_document' for s in registry),
                   accepted_facts=len(facts), pending_fact_codings=sum(c['publication_status']!='accepted' for c in checks),
                   coverage_cells=len(coverage), cells_with_partial_evidence=sum(c['evidence_rows']>0 for c in coverage),
                   missing_cells=sum(c['evidence_rows']==0 for c in coverage), all_25_city_task_complete=False)
    summary['physical_school_lea_city_queue_rows'] = len(lea_groups)
    (OUT / 'education_access_validation.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    assert len(cities)==25
    assert all(len(r['city_id'])==7 and r['city_id'] in cities for r in facts)
    assert len({r['record_id'] for r in facts})==len(facts)
    assert all(r['value']=='' for r in facts)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
