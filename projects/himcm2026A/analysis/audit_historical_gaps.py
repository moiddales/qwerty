"""Recheck named historical gaps against preserved observations and new official evidence."""
import csv
import gzip
import json
from collections import Counter
from collect_supplement_sources import PROJECT, SUPPLEMENT, write_json

folder = SUPPLEMENT / "historical_gaps"
latest = {row["placefips"]: row for row in json.loads((folder / "places_2025_25cities_local_requery.json").read_text(encoding="utf-8"))}
with gzip.open(PROJECT / "data/processed/observations_all_levels.csv.gz", "rt", encoding="utf-8-sig") as stream:
    previous = [row for row in csv.DictReader(stream) if row["source_id"] == "S15"]
missing = [row for row in previous if row["value"] == ""]
assert len(latest) == 25 and len(missing) == 210
rows = []
for row in missing:
    field = row["indicator_id"].lower()
    current = latest[row["city_id"]].get(field, "")
    assert current == "", (row["city_id"], field, current)
    reason = "2023 BRFSS-based estimates not published for Pennsylvania; CDC release notes" if row["city_id"] == "4260000" else "Seven health-related-social-needs measures absent from this state's published 2025 place data; module participation cause still being checked"
    rows.append(dict(city_id=row["city_id"], city_name=row["city_name"], indicator_id=row["indicator_id"],
                     original_value="", current_value=current, source_period="PLACES December 2025 release",
                     age_universe="adults; not adolescent outcome", missing_classification="specified_source_version_has_no_estimate",
                     evidence="places_2025_25cities_local_requery.json; CDC current-release-notes",
                     reason=reason, treatment="Retain missing; do not substitute adult estimates for teen outcomes or silently use older years"))
with (folder / "places_210_missing_recheck.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
cities = list(csv.DictReader((PROJECT / "data/metadata/cities.csv").open(encoding="utf-8-sig")))
fars = [dict(city_id=city["city_id"], city_name=city["city_name"], target="2025 FARS Annual Reporting File city crash/person records",
             collection_status="not_yet_published_under_official_release_schedule", expected_release="early 2027",
             evidence_url="https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/813778", evidence_page="1",
             local_evidence="raw_local/nhtsa_2025_first9months_813778.pdf", local_access="HTTP200 valid PDF",
             index_access="local NHTSA index HTTP403; official web channel lists years through2024",
             available_comparable_window="2021-2024 retained from base archive",
             value="", treatment="No national early estimate assigned to a city") for city in cities]
with (folder / "fars_2025_25city_publication_status.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(fars[0])); writer.writeheader(); writer.writerows(fars)
write_json(folder / "historical_gap_validation.json", dict(places_source_rows=len(latest), places_original_records=len(previous),
    places_missing_rechecked=len(rows), places_missing_by_city=dict(Counter(row["city_id"] for row in rows)),
    fars_cities_with_explicit_publication_status=len(fars), all_historical_gaps_closed=False))
print("Rechecked", len(rows), "PLACES gaps; recorded FARS release boundary for", len(fars), "cities")
