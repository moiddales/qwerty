"""Retrieve official sample-program evidence; publish facts, not source-page copies.

Run from the repository root. Input facts are manually checked against the listed
official pages; this script records local HTTP/content checks and builds CSVs.
"""
from __future__ import annotations

import argparse
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import fitz
import requests
from lxml import html

ROOT = Path(__file__).resolve().parents[1] / "supplement_20261111" / "youth_services"
FIELDS = ["record_id", "city_id", "census_city_name", "population_rank", "city", "state", "domain", "provider", "program", "evidence_scope", "age_min", "age_max", "age_grade_rule", "residence_eligibility", "location", "fee_usd", "fee_unit", "fee_rule", "reduction_rule", "schedule", "registration_appointment", "referral_rule", "insurance_rule", "self_pay_rule", "capacity_number", "capacity_unit", "capacity_rule", "wait_days", "wait_rule", "observation_period", "source_ids", "quality_note"]


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fetch(source):
    sid = source["source_id"]
    checked_at = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
    evidence = dict(source, checked_at=checked_at, environment="user_local_windows_python_requests", request_method="GET", http_status="", final_url="", content_type="", downloaded_bytes="", raw_local_path="", parsed_local_path="", parse_status="", marker_status="", error="", source_republication="excluded; short independently encoded facts only")
    try:
        response = requests.get(source["url"], timeout=40, headers={"User-Agent": "Mozilla/5.0 (compatible; academic public-data collection)"})
    except requests.RequestException as exc:
        evidence.update(parse_status="request_failed", error=str(exc))
        return evidence
    evidence.update(http_status=response.status_code, final_url=response.url, content_type=response.headers.get("content-type", ""), downloaded_bytes=len(response.content))
    suffix = ".pdf" if response.content.startswith(b"%PDF") else ".html"
    raw_path = ROOT / "raw_local" / (sid + suffix)
    raw_path.write_bytes(response.content)
    evidence["raw_local_path"] = raw_path.relative_to(ROOT).as_posix()
    if response.status_code != 200:
        evidence["parse_status"] = "http_error_response_saved_locally"
        return evidence
    if suffix == ".pdf":
        with fitz.open(stream=response.content, filetype="pdf") as document:
            content = "\n".join(page.get_text() for page in document)
        evidence["parse_status"] = "pdf_text_parsed" if content.strip() else "pdf_without_extracted_text"
    else:
        tree = html.fromstring(response.content)
        for element in tree.xpath("//script|//style|//noscript"):
            element.drop_tree()
        content = tree.text_content()
        evidence["parse_status"] = "html_text_parsed"
    parsed_path = ROOT / "raw_local" / (sid + ".txt")
    parsed_path.write_text(content, encoding="utf-8")
    evidence["parsed_local_path"] = parsed_path.relative_to(ROOT).as_posix()
    normalized = " ".join(content.lower().split())
    evidence["marker_status"] = "present" if " ".join(source["content_marker"].lower().split()) in normalized else "not_found_review_required"
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "raw_local").mkdir(exist_ok=True)
    data = [row for path in sorted(ROOT.glob("program_facts*.json")) for row in json.loads(path.read_text(encoding="utf-8"))]
    sources = [row for path in sorted(ROOT.glob("sources*.json")) for row in json.loads(path.read_text(encoding="utf-8"))]
    source_ids = {s["source_id"] for s in sources}
    assert len(source_ids) == len(sources)
    assert len({r["record_id"] for r in data}) == len(data)
    for row in data:
        assert set(row) <= set(FIELDS), set(row) - set(FIELDS)
        assert set(row["source_ids"].split(";")) <= source_ids
        assert row["evidence_scope"]
    with (ROOT.parents[1] / "data" / "metadata" / "cities.csv").open(encoding="utf-8-sig", newline="") as stream:
        cities = list(csv.DictReader(stream))
    aliases = {"Indianapolis city (balance)": "Indianapolis (balance)", "Nashville-Davidson metropolitan government (balance)": "Nashville-Davidson (balance)"}
    city_lookup = {aliases.get(c["city_name"], c["city_name"].removesuffix(" city")): c for c in cities}
    for row in data:
        city = city_lookup[row["city"]]
        assert row["state"] == city["state_abbr"]
        row.update(city_id=city["city_id"], census_city_name=city["city_name"], population_rank=city["population_rank"])
    if args.fetch:
        evidence_path = ROOT / "access_evidence.json"
        previous = {e["source_id"]: e for e in json.loads(evidence_path.read_text(encoding="utf-8"))} if evidence_path.exists() else {}
        pending = [s for s in sources if s["source_id"] not in previous]
        with ThreadPoolExecutor(max_workers=6) as executor:
            fresh = {e["source_id"]: e for e in executor.map(fetch, pending)}
        evidence = [previous[s["source_id"]] if s["source_id"] in previous else fresh[s["source_id"]] for s in sources]
        (ROOT / "access_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        evidence = json.loads((ROOT / "access_evidence.json").read_text(encoding="utf-8"))
    write_csv(ROOT / "program_conditions.csv", data, FIELDS)
    evidence_fields = list(dict.fromkeys(key for row in evidence for key in row))
    write_csv(ROOT / "source_access_evidence.csv", evidence, evidence_fields)
    coverage = []
    for city in dict.fromkeys(r["city"] for r in data):
        for domain in ("activity", "mental_health"):
            records = [r for r in data if r["city"] == city and r["domain"] == domain]
            coverage.append(dict(city_id=records[0]["city_id"], census_city_name=records[0]["census_city_name"], city=city, domain=domain, sample_records=len(records), published_wait_measurements=sum(r.get("wait_days", "") != "" for r in records), published_capacity_numbers=sum(r.get("capacity_number", "") != "" for r in records), scope="named official program sample; no citywide representativeness"))
    write_csv(ROOT / "city_domain_coverage.csv", coverage, list(coverage[0]))
    field_coverage = [dict(domain=domain, field=field, nonempty_records=sum(r.get(field, "") != "" for r in data if r["domain"] == domain), total_records=sum(r["domain"] == domain for r in data), interpretation="Nonempty text may describe an unresolved condition; inspect record and quality_note") for domain in ("activity", "mental_health") for field in FIELDS if field not in ("record_id", "city_id", "census_city_name", "population_rank", "city", "state", "domain")]
    write_csv(ROOT / "field_coverage.csv", field_coverage, list(field_coverage[0]))
    native_path = ROOT / "curl_access_evidence.json"
    native_checks = json.loads(native_path.read_text(encoding="utf-8")) if native_path.exists() else []
    locally_valid = {r["source_id"] for r in evidence + native_checks if r["http_status"] == 200 and r["marker_status"] == "present"}
    referenced = {sid for row in data for sid in row["source_ids"].split(";")}
    summary = dict(checked_at=datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"), cities=len({r["city"] for r in data}), records=len(data), sources=len(sources), locally_http_200=sum(r["http_status"] == 200 for r in evidence), locally_marker_present=sum(r["marker_status"] == "present" for r in evidence), native_curl_valid_sources=sum(r["http_status"] == 200 and r["marker_status"] == "present" for r in native_checks), locally_valid_unique_sources=len(locally_valid), unresolved_local_sources=[dict(source_id=s["source_id"], referenced_by_current_record=s["source_id"] in referenced) for s in sources if s["source_id"] not in locally_valid], source_errors=[{"source_id": r["source_id"], "http_status": r["http_status"], "parse_status": r["parse_status"], "marker_status": r["marker_status"], "error": r["error"]} for r in evidence if r["http_status"] != 200 or r["marker_status"] != "present"])
    (ROOT / "validation.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
