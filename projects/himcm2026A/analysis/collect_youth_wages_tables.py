"""Rebuild the manually source-coded youth wage tables. No network requests.

Rates are statutory facts for named reference jobs, not observed earnings or
unconditional city-wide youth wages. Official originals remain in raw_local.
"""
import csv
import json
from decimal import Decimal
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'supplement_20261111/wages'
AS_OF = '2026-11-11'
SOURCES = {s['source_id']: s for s in json.loads((ROOT / 'sources.json').read_text(encoding='utf-8'))}
SCENARIO = ('Lawfully employed, covered private-sector, ordinary non-tipped nonagricultural job; '
            'outside initial training/learner period, special certificate, subsidized program, '
            'public contract and industry-specific higher wage; local work-hour threshold met.')


def write_csv(name, rows):
    with (ROOT / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


# State reference facts. Local rules below supersede them for covered city work.
STATE = {
    'NY': ('17.00', '2026-01-01', 'NY_NYC|NY_TIPPED|NY_MINORS', 'NYC state regional rate; every employer size.'),
    'CA': ('16.90', '2026-01-01', 'CA_FAQ', 'All employer sizes; applicable higher city/industry rate takes priority.'),
    'IL': ('15.00', '2025-01-01', 'IL_FAQ', 'State generally 4+ employees; under18 <=650 employer-hours/calendar-year $13; >650 $15.'),
    'TX': ('7.25', '2009-07-24', 'TX_RATE|TX_YOUTH', 'FLSA-covered employment excluded from state Act; some youth/student and industry state exclusions.'),
    'AZ': ('15.15', '2026-01-01', 'AZ_RATE|AZ_LAW|AZ_DEFINITIONS|AZ_YOUTH_FAQ', 'Small business exemption requires both revenue <$500000 and exemption from federal minimum wage; parent/sibling employment and casual home babysitting excluded.'),
    'PA': ('7.25', '2009-07-24', 'PA_TRAINING|PA_STUDENTS|PA_TIP', 'General state minimum; approved student/learner certificates separately.'),
    'FL': ('15.00', '2026-09-30', 'FL_RATE|US_STATE', 'FLSA-entitled employees; $14 until 2026-09-29; latest $15 through 2027-12-31.'),
    'NC': ('7.25', '2009-07-24', 'NC_RATE|NC_LAW|NC_STUDENTS|NC_PREEMPT', 'General state minimum; specific student/learner/apprentice/messenger and statutory exemptions separately.'),
    'OH': ('11.00', '2026-01-01', 'OH_OFFICIAL_POSTER|OH_RATE|OH_PREEMPT', 'State higher rate excludes under16 and employers below $405000 gross; exactly $405000 source wording conflict retained.'),
    'IN': ('7.25', '2009-07-24', 'IN_POSTER', 'FLSA or Indiana Minimum Wage Law coverage must be established.'),
    'WA': ('17.13', '2026-01-01', 'WA_RATE', 'State 14-15 rate 85%; higher Seattle rules apply to covered city work.'),
    'CO': ('15.16', '2026-01-01', 'US_STATE|CO_LOCAL', 'State unemancipated minor reduction differs from Denver certified-program restriction.'),
    'TN': ('', '', 'TN_RATE|US_STATE', 'No state minimum wage; federal coverage determines entitlement.'),
    'OK': ('7.25', '2009-07-24', 'OK_RULE|OK_POSTER', 'State excludes under18 nongraduates, enrolled students under22, and nonpermanent <25h/week employees; federal coverage remains separate.'),
    'DC': ('18.40', '2026-07-01', 'DC_RATE', 'District rate; under18 may receive federal minimum; special youth-employment statutes separately.'),
    'NV': ('12.00', '2024-07-01', 'NV_2026|NV_APPROVED|NV_CONST', 'Under18, nonprofit afterschool/summer, <=90day trainee and clear CBA waivers excluded by approved2026 regulation.'),
    'MA': ('15.00', '2023-01-01', 'MA_LAW|MA_SERVICE|MA_YOUTH|MA_PAY', 'Covered occupations; agricultural work and commissioner-approved learner/apprentice schedules separately.')
}


def city_profile(city):
    state = city['state_abbr']
    rate, start, ids, condition = STATE[state]
    result = dict(
        population_rank=city['population_rank'], city_id=city['city_id'], city_name=city['city_name'],
        state_abbr=state, as_of_date=AS_OF, unit='USD/hour gross statutory minimum',
        reference_scenario=SCENARIO, work_geography='Actual job location; city residence alone does not determine wage.',
        applicable_reference_level='state', state_general_rate=rate, state_rate_effective_from=start,
        federal_general_rate='7.25', federal_rate_effective_from='2009-07-24',
        city_general_rate='', city_rate_effective_from='',
        age_14_15_reference_rate=rate, age_16_17_reference_rate=rate, age_18_reference_rate=rate,
        youth_rate_basis='Same general rate for reference job; separate exceptions below.',
        initial_period_rule='Federal $4.25 under20 first90 calendar days cannot displace a higher applicable state/local requirement.',
        age18_tipped_cash_reference_rate='', tipped_rule='', employer_coverage=condition,
        industry_and_program_rules='', local_general_rule_status='State/federal reference; local specialized contract rates excluded.',
        source_version_note='Official rates effective in2026 where published; access date is not effective date.',
        evidence_status='official source coded; local access stages recorded separately', unresolved_fields='',
        source_ids=ids + '|US_GUIDE|US_YOUTH', source_urls='')
    if state == 'TX':
        result.update(age18_tipped_cash_reference_rate='2.13',
                      initial_period_rule='Verified federal youth wage $4.25: under20, first90 consecutive calendar days, no displacement; TXWC June2025 guidance.',
                      tipped_rule='FLSA tipped job: >$30/month tips, required notice and retained tips; cash+tips >=$7.25, employer covers shortfall.',
                      local_general_rule_status='Texas Labor Code62.0515 preempts general private-employment local wage; public-contract/training exceptions retained.',
                      industry_and_program_rules='Agriculture, domestic work, nonprofit and recreational jobs have coverage exemptions; public contracts can set other wages.',
                      source_ids=result['source_ids'] + '|TX_PREEMPT',
                      source_version_note='TXWC general current page; youth explanation June2025, not a new2026 rate.')
    if state == 'NY':
        result.update(age18_tipped_cash_reference_rate='11.35',
                      tipped_rule='Hospitality food-service cash $11.35; hospitality service-worker cash $14.15; total >=$17 and tip-credit conditions apply; other jobs $17.',
                      industry_and_program_rules='NYDOL 2026 minors handbook covers general jobs; farm hand-harvest/family and wage-order allowances are distinct.',
                      local_general_rule_status='NYC $17 is a New York STATE regional rule, not an additional city ordinance.')
    if state == 'CA':
        result.update(tipped_rule='California forbids tip credit; cash wage must reach applicable minimum.',
                      initial_period_rule='State learners without similar prior experience:85% rounded nearest nickel for first160 employment-hours, any age; local application separately.',
                      industry_and_program_rules='Covered fast-food chains $20 from2024-04-01; covered healthcare employer schedules and higher local industry rates apply.',
                      source_ids=result['source_ids'] + '|CA_FASTFOOD|CA_HEALTH')
    if state == 'AZ':
        result.update(age18_tipped_cash_reference_rate='12.15',
                      tipped_rule='Up to$3 credit only when tips+cash meet$15.15 and employer records prove it.',
                      initial_period_rule='General Arizona age-neutral state minimum governs covered jobs; federal$4.25 does not reduce this rate.',
                      source_version_note='2026 ICA rate; age equality FAQ is2017 source, combined with current statutory employee definition.',
                      unresolved_fields='No Phoenix-specific general ordinance located; local contracted/prevailing wages not inventoried.')
    if state == 'PA':
        result.update(age18_tipped_cash_reference_rate='2.83',
                      tipped_rule='PA tip-credit conditions apply; employer must make up shortfall to$7.25.',
                      initial_period_rule='34 Pa Code231.103 forbids the former training wage after2009-07-23; ordinary initial employment remains$7.25.',
                      industry_and_program_rules='Special state student certificate permits>=85% and <=20h/week during term (holiday expansion max40h); federal certification separately if covered.',
                      unresolved_fields='City/public-contractor living wage is a separate job class; not exhaustively inventoried.')
    if state == 'FL':
        result.update(age18_tipped_cash_reference_rate='11.98',
                      tipped_rule='Eligible tipped employee>$30/month:cash$11.98 plus tips to$15; maximum tip credit$3.02. USDOL current table web-index read.',
                      initial_period_rule='No general Florida youth/training reduction verified; ordinary covered14-18 reference job uses$15.',
                      source_ids=result['source_ids']+'|US_TIPPED|FL_STATUTE',
                      unresolved_fields='2026 poster direct access403; precise Florida youth/certificate overlay not fully coded.',
                      evidence_status='Official 2026 rate web-index verified; local FloridaCommerce HTTP403')
    if state == 'NC':
        result.update(age18_tipped_cash_reference_rate='2.13',
                      tipped_rule='Cash+tips >=$7.25; advance notice and records; employer covers shortfall.',
                      initial_period_rule='Do not automatically apply federal$4.25:GS95-25.14(a)(1)b restores state floor when federal applicable rate lower, except named categories.',
                      industry_and_program_rules='GS95-25.3(b): full-time students/learners/apprentices/messengers as federally defined90% rounded DOWN to nickel ($6.50 of$7.25), subject to coverage.',
                      local_general_rule_status='GS95-25.1 local private compensation rules preempted; local government employee rules separate.')
    if state == 'OH':
        result.update(age_14_15_reference_rate='7.25', age18_tipped_cash_reference_rate='5.50',
                      youth_rate_basis='Official2026 poster:under16 federal$7.25; age16+ higher state rate where employer revenue threshold met.',
                      tipped_rule='State covered tipped reference age18 cash$5.50, total >=$11; younger/small-employer tip overlay not resolved.',
                      initial_period_rule='Poster expressly says under16 not less than current federal$7.25; no$4.25 Ohio training reduction assigned.',
                      local_general_rule_status='ORC4111.02 forbids local minimum different from state rule.',
                      unresolved_fields='Exactly$405000 boundary:poster says below; state2025 news says$405000-or-less; use >$405000 reference employers.')
    if state == 'IN':
        result.update(age18_tipped_cash_reference_rate='2.13',
                      initial_period_rule='Official Indiana poster:under20 first90 consecutive calendar-days$4.25; then ordinary$7.25.',
                      tipped_rule='When tip credit claimed cash >=$2.13 and cash+tips >=$7.25; employer covers shortfall.',
                      source_version_note='Official poster identifies effective2009 rate; no new2026 statutory rate claimed.')
    if state == 'TN':
        result.update(applicable_reference_level='federal conditional on FLSA coverage',
                      age_14_15_reference_rate='7.25',age_16_17_reference_rate='7.25',age_18_reference_rate='7.25',
                      age18_tipped_cash_reference_rate='2.13',
                      initial_period_rule='FLSA-covered under20 first90 consecutive calendar-days$4.25 with anti-displacement conditions.',
                      tipped_rule='FLSA coverage/tip-credit requirements:cash$2.13; total$7.25; employer covers shortfall.',
                      industry_and_program_rules='FLSA exemptions include certain seasonal recreation/camp and casual babysitting work; no universal federal floor if exempt.')
    if state == 'OK':
        result.update(applicable_reference_level='federal conditional on FLSA coverage for student reference job',
                      age18_tipped_cash_reference_rate='2.13',
                      initial_period_rule='State youth/student exclusions do not erase FLSA:covered under20 first90days federal$4.25 with no displacement; otherwise$7.25.',
                      tipped_rule='Federal-covered ordinary tipped job cash$2.13; total$7.25; employer covers shortfall.',
                      industry_and_program_rules='Nongraduate under18, enrolled under22 and nonpermanent<25h/week are state exclusions; state coverage employer10+FTE or revenue>$100000.',
                      source_version_note='OKDOL current FAQ has obvious2000 effective-date typo; federal2009 date retained from USDOL.',
                      unresolved_fields='No floor assigned where both state and federal protections exclude the job.')
    if state == 'DC':
        result.update(age_14_15_reference_rate='7.25', age_16_17_reference_rate='7.25', age18_tipped_cash_reference_rate='10.30',
                      youth_rate_basis='DCOAG expressly permits under18 federal minimum; age18 district general minimum.',
                      initial_period_rule='Under18 federal-wage exception verified; under20 first90day$4.25 interaction not resolved, so no lower numeric DC training rate assigned.',
                      tipped_rule='Ordinary district-covered age18 cash$10.30, tips+cash >=$18.40; under18 tipped cash treatment unresolved.',
                      industry_and_program_rules='Youth Employment Act and other named statutory programs set separate wages; higher-education student-employees federal wage exception.')
    if state == 'NV':
        result.update(age_14_15_reference_rate='7.25', age_16_17_reference_rate='7.25', age18_tipped_cash_reference_rate='12.00',
                      youth_rate_basis='R185-24AP filed2026-04-29 excludes under18; reference young job is FLSA-covered and past90days.',
                      initial_period_rule='Approved2026 NAC608.100 excludes<=90day FLSA6(g) trainees; eligible federal-covered under20 trainees$4.25.',
                      tipped_rule='Covered state minimum cannot be met with tips; age18 reference cash$12. Under18/state-exempt tipped overlay not assigned.',
                      industry_and_program_rules='Approved rule also exempts nonprofit afterschool/summer jobs and unambiguous valid CBA waiver; federal obligations still separately apply.',
                      source_version_note='2026 bulletin table July1,2026; body saysJuly1,2025; constitutional$12 effective2024-07-01. Current approved regulation used over stale consolidatedNAC.')
    if state == 'MA':
        result.update(age18_tipped_cash_reference_rate='6.75',
                      tipped_rule='Service rate$6.75 only if tip conditions met; shift total must reach$15 and employer makes up difference.',
                      initial_period_rule='General covered youth job$15; commissioner-authorized learner/apprentice scales in c151s7 are conditional, not automatic federal$4.25.',
                      industry_and_program_rules='Agriculture$8 per Mass.gov; institutional training/religious/professional exclusions and approved learner schedules separate.',
                      source_version_note='2023 general rate retained; Massachusetts Legislature HTML locally200; Mass.gov explanatory pages403.',
                      unresolved_fields='Current special learner certificate schedules and every occupational exemption not fully coded.')
    cid = city['city_id']
    locals_ = {
        '0644000': ('18.42','2026-07-01','LA_RATE|LA_FAQ|LA_HOTEL','At least2 hours work in city in a particular week.'),
        '0666000': ('17.75','2026-01-01','SD_RATE|SD_FAQ','At least2 city work-hours in one or more calendar weeks/year.'),
        '0668000': ('18.45','2026-01-01','SJ_RATE|SJ_COUNTY','City-covered work; exact current employer nexus/learner details still flagged.'),
        '0667000': ('19.61','2026-07-01','SF_RATE','At least2 hours/week in San Francisco.'),
        '1714000': ('17.05','2026-07-01','CHI_MW_ALT|CHI_PRESS','Employers4+employees; domestic workers separately protected.'),
        '5363000': ('21.30','2026-01-01','SEA_RATE|SEA_YOUTH','Work within Seattle; all employer sizes same rate since2025.'),
        '0820000': ('19.29','2026-01-01','DEN_RATE','At least4 hours/week within City and County of Denver; passing through excluded.')}
    if cid in locals_:
        wage, effective, local_ids, threshold = locals_[cid]
        result.update(applicable_reference_level='city', city_general_rate=wage, city_rate_effective_from=effective,
                      age_14_15_reference_rate=wage,age_16_17_reference_rate=wage,age_18_reference_rate=wage,
                      employer_coverage=threshold+' '+condition, source_ids=result['source_ids']+'|'+local_ids,
                      local_general_rule_status='Higher city rule verified for reference scenario.')
        if state in ('CA','WA'):
            result['age18_tipped_cash_reference_rate'] = wage
    if cid == '0644000':
        result.update(initial_period_rule='LA14-17:first160 employment-hours city floor85% rounded nearest nickel=$15.65. Final wage>=applicable state floor;15.65 requires eligible state learner(no similar prior experience), otherwise state16.90. Age18 city reduction not established.',
                      industry_and_program_rules=result['industry_and_program_rules']+' LA covered hotels60+rooms (50+AHEZ):cash$25 plus$4.25 health benefit from2026-07-01; unpaid benefit difference becomes cash.',
                      source_version_note='Current2026 rate; FAQ attachment uploaded2026 internally datedJuly2024; youth text retained with explicit source vintage.',
                      unresolved_fields='Local treatment of state learners age18; health/fast-food learner interactions not given automatic reduced numeric wage.')
    if cid == '0666000':
        result.update(industry_and_program_rules=result['industry_and_program_rules']+' City excludes publicly subsidized summer/short-term youth programs and specified camp/student employees;2026FAQ q7.',
                      unresolved_fields='California160hour learner rule relationship to city wage unresolved; no reduced city learner number assigned.')
    if cid == '0668000':
        result.update(evidence_status='City2026 rate web-index verified; local city page403; official Santa Clara County table200 confirms18.45',
                      unresolved_fields='Current SanJose learner/certificate/CBA exceptions and exact employer nexus not independently resolved.')
    if cid == '0667000':
        result.update(industry_and_program_rules=result['industry_and_program_rules']+' SF government-subsidized bona fide afterschool/summer training/apprenticeship under18:$17.35 from2026-07-01.',
                      source_ids=result['source_ids']+'|SF_POSTER',
                      unresolved_fields='Ordinary CA160hour learner interaction with SF city ordinance unresolved; no general youth discount assigned.')
    if cid == '1714000':
        result.update(age_14_15_reference_rate='17.05',age_16_17_reference_rate='17.05', age18_tipped_cash_reference_rate='12.96',
                      youth_rate_basis='6-105-020(b)(3)(F) raises2025youth$16.50 by up to$1.50 annually until matching general rate;2026youth therefore17.05.',
                      initial_period_rule='6-105-010 excludes ordinary initial90day state4(a)(2) workers, except specified day/temp/seasonal categories; state18+non-tip initial rate14.50 can apply. Under18 ordinary job city17.05.',
                      tipped_rule='Ordinary city-covered worker cash$12.96, total$17.05;6-105-030 allows24%credit through2028-06-30. Initial-period coverage evaluated separately.',
                      employer_coverage='4+employees; at least2hours in any particular2week period physically in Chicago; all domestic workers included. State/federal coverage separately.',
                      industry_and_program_rules='City public-contract/concessionaire$18.50 from2026-07-01; subsidy youth/transitional programs same city rate. Stipend day-camp counselor with guardian consent excluded.',
                      source_ids=result['source_ids']+'|CHI_CODE_WAGE|CHI_CODE_DEF|CHI_CODE_TIP',
                      source_version_note='Current2026S75 municipal code directly read with web tool; annual city rate verified by local200 officialBACPHTML; cityposter/FAQ403.',
                      unresolved_fields='Initial90day tipped/state learner program interactions must use job-specific coverage; not combined into one floor.')
    if cid == '5363000':
        result.update(age_14_15_reference_rate='18.105',
                      youth_rate_basis='Exact derived85%*21.30=18.105;16-17same as adults; source2018officialFAQ. Cents-rounding not asserted.',
                      initial_period_rule='No automatic federal90day$4.25; Seattle special certificate requires state certificate and OLS approval; do not infer from state certificate alone.',
                      tipped_rule='No tip/medical-benefit offset; wage requirement met before tips.',
                      industry_and_program_rules='Seattle special certificate for eligible learners/apprentices/messengers is a separate approval path.',
                      source_version_note='2026 cityrate combined with2018officialageFAQ and currentWAage14-15rule;18.105is formula output not an officially quoted cent rate.',
                      unresolved_fields='2026 cent-rounding rule for85% calculation; currentageFAQ revision after2018 not obtained.')
    if cid == '0820000':
        result.update(age18_tipped_cash_reference_rate='16.27',
                      initial_period_rule='Only unemancipated minors doing city-certified youth program work may be paid up to15% below city minimum; ordinary minor stays19.29.',
                      tipped_rule='Food/beverage only:credit <=$3.02 actually earned;cash$16.27 and total$19.29; other tipped jobs full applicable wage.',
                      industry_and_program_rules='Certified youth program reduction formula19.29*0.85=16.3965; emancipation and city certification required; no ordinary-youth reduction.',
                      unresolved_fields='Rounding/stacking of certified-program reduction and tipped credit not numerically applied.')
    unique_ids = list(dict.fromkeys(result['source_ids'].split('|')))
    result['source_ids'] = '|'.join(unique_ids)
    result['source_urls'] = '|'.join(SOURCES[s]['url'] for s in unique_ids)
    return result


def main():
    with (BASE/'data/metadata/cities.csv').open(encoding='utf-8-sig') as stream:
        cities = list(csv.DictReader(stream))
    rows = [city_profile(city) for city in cities]
    write_csv('city_youth_wage_rules_25cities.csv', rows)
    logs = [json.loads(line) for line in (ROOT/'access_log.jsonl').read_text(encoding='utf-8').splitlines()]
    latest = {item['source_id']: item for item in logs}
    coverage = []
    for row in rows:
        ids = row['source_ids'].split('|')
        coverage.append(dict(city_id=row['city_id'], city_name=row['city_name'],
            age14_15_numeric=int(bool(row['age_14_15_reference_rate'])),
            age16_17_numeric=int(bool(row['age_16_17_reference_rate'])),
            age18_numeric=int(bool(row['age_18_reference_rate'])),
            initial_period_coded=1, tipped_conditions_coded=1, employer_conditions_coded=1,
            industry_or_program_conditions_coded=int(bool(row['industry_and_program_rules'])),
            source_count=len(ids), locally_confirmed_sources=sum(latest[s]['fetch_stage']=='downloaded_content_confirmed' for s in ids),
            open_qualification=row['unresolved_fields']))
    write_csv('coverage_25cities.csv', coverage)
    dictionary = {
        'population_rank':'Frozen Census V2025 population rank.',
        'city_id':'Seven-character state+place Census ID; preserve leading zeroes.',
        'city_name':'Frozen city name, including Census balance.',
        'state_abbr':'US postal abbreviation; DC is district.',
        'as_of_date':'Date at which the source-coded reference scenario is compared, YYYY-MM-DD.',
        'unit':'USD per hour gross statutory wage, not observed earnings.',
        'reference_scenario':'The common employment scenario required for numeric age reference columns.',
        'work_geography':'Actual place of work determines geographic wage entitlement; residence is not sufficient.',
        'applicable_reference_level':'Controlling level for the named reference job; city, state, or conditional federal.',
        'state_general_rate':'General state/district floor before youth/local/industry exceptions; blank for TN no state law.',
        'state_rate_effective_from':'Start date of coded state general rate; not download date.',
        'federal_general_rate':'FLSA-covered ordinary nonexempt floor before youth/tip/certificate exceptions.',
        'federal_rate_effective_from':'Federal general rate effective date.',
        'city_general_rate':'Higher citywide general rate if a city rule is explicitly coded; blank is not zero.',
        'city_rate_effective_from':'Start of coded city general rate, not original ordinance adoption date.',
        'age_14_15_reference_rate':'Reference job age14-15 rate; Seattle18.105 is exact85% formula, cent rounding unresolved.',
        'age_16_17_reference_rate':'Reference job age16-17 rate conditional on coverage and absence of named exceptions.',
        'age_18_reference_rate':'Reference job age18 rate, past initial youth/training period.',
        'youth_rate_basis':'Why age groups share or differ in rates; identifies derivation and source vintage.',
        'initial_period_rule':'Initial calendar-day/employment-hour or approved-training rule; these units must not be interchanged.',
        'age18_tipped_cash_reference_rate':'Age18 employer direct cash floor under named tip conditions; tips are additional and employer covers shortfall.',
        'tipped_rule':'Tip credit eligibility and total-wage condition; age18 values do not automatically cover under18.',
        'employer_coverage':'Headcount/revenue/location/hour-threshold and employee-coverage constraints.',
        'industry_and_program_rules':'Separately coded industry, subsidized youth, certificate, family, camp or public-contract classes.',
        'local_general_rule_status':'Evidence for the city/state relationship; partial local-special-rule searches stay explicit.',
        'source_version_note':'Document revision, temporal mismatch, calculation and source typo qualifications.',
        'evidence_status':'Source content reading status; inspect access logs for actual local HTTP and parse stage.',
        'unresolved_fields':'Named remaining wage-rule qualification; blank indicates no additional unresolved item recorded.',
        'source_ids':'Pipe-delimited IDs in sources.json; source facts also have locally tested access metadata.',
        'source_urls':'Pipe-delimited original official URLs aligned with source_ids.'}
    write_csv('field_dictionary.csv',[dict(field=key,definition=dictionary[key],missing_value='empty string; never zero-imputed') for key in rows[0]])
    write_csv('source_access_latest.csv', [dict(source_id=sid, title=source['title'], url=source['url'],
        http_status=latest[sid]['http_status'], fetched_at_utc=latest[sid]['requested_at_utc'],
        fetch_stage=latest[sid]['fetch_stage'], parse_stage=latest[sid]['parse_stage'],
        raw_local_path=latest[sid]['raw_local_path'], parsed_local_path=latest[sid]['parsed_local_path'],
        redistribution='Short factual coding and URL only; source originals excluded from Git.') for sid,source in SOURCES.items()])
    assert len(rows) == len({r['city_id'] for r in rows}) == 25
    assert {r['city_id'] for r in rows} == {r['city_id'] for r in cities}
    for row in rows:
        for key in ('age_14_15_reference_rate','age_16_17_reference_rate','age_18_reference_rate'):
            if row[key]: assert Decimal(row[key]) > 0
        assert row['reference_scenario'] and row['initial_period_rule'] and row['employer_coverage'] and row['tipped_rule']
    validation = dict(as_of_date=AS_OF, city_rows=25, age14_15_numeric=sum(r['age14_15_numeric'] for r in coverage),
        age16_17_numeric=sum(r['age16_17_numeric'] for r in coverage), age18_numeric=25,
        source_count=len(SOURCES), access_attempts=len(logs),
        locally_confirmed_sources=sum(r['fetch_stage']=='downloaded_content_confirmed' for r in latest.values()),
        checks=['25 exact frozen city IDs; all rows conditional; linked source IDs exist; age-rate values positive',
                'No index/ranking or earnings forecast produced; unresolved youth/tip/training overlays stay explicit'])
    (ROOT/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(validation,ensure_ascii=False))


if __name__ == '__main__':
    main()
