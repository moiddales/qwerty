"""Validate the public-use NHTS tables and preserve the 14-18 subset."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import zipfile
from collect_supplement_sources import PROJECT, SUPPLEMENT, write_json


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    folder = SUPPLEMENT / "nhts"
    tables = {}
    inventory = []
    dictionary = []
    with zipfile.ZipFile(folder / "raw/nhts_2022_v2_1_csv.zip") as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if not name.endswith(".csv"):
                continue
            data = archive.read(name)
            reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
            rows = list(reader)
            assert rows
            tables[name] = rows
            inventory.append(dict(file=name, rows=len(rows), columns=len(reader.fieldnames),
                                  bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
            dictionary.extend(dict(table=name, field=field, type="source string; retain codes",
                                   definition_source="2022 public-use codebook V2.1 (April 2025)")
                              for field in reader.fieldnames)
    hh = tables["hhv2pub.csv"]
    persons = tables["perv2pub.csv"]
    trips = tables["tripv2pub.csv"]
    household_ids = {row["HOUSEID"] for row in hh}
    person_ids = {(row["HOUSEID"], row["PERSONID"]) for row in persons}
    assert len(household_ids) == len(hh)
    assert len(person_ids) == len(persons)
    assert all(row["HOUSEID"] in household_ids for row in persons)
    assert all((row["HOUSEID"], row["PERSONID"]) in person_ids for row in trips)
    assert all(float(row["WTPERFIN"]) > 0 for row in persons)
    assert all(float(row["WTTRDFIN"]) > 0 for row in trips)
    youth = [row for row in persons if 14 <= int(row["R_AGE"]) <= 18]
    youth_ids = {(row["HOUSEID"], row["PERSONID"]) for row in youth}
    youth_trips = [row for row in trips if (row["HOUSEID"], row["PERSONID"]) in youth_ids]
    for name, rows in [("persons_age14_18.csv.gz", youth), ("trips_age14_18.csv.gz", youth_trips)]:
        with gzip.open(folder / name, "wt", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    write_csv(folder / "table_inventory.csv", inventory, list(inventory[0]))
    write_csv(folder / "field_dictionary.csv", dictionary, list(dictionary[0]))
    cities = list(csv.DictReader((PROJECT / "data/metadata/cities.csv").open(encoding="utf-8-sig")))
    coverage = [dict(city_id=city["city_id"], city_name=city["city_name"], version="2022 V2.1 April 2025",
                     microdata_status="downloaded_parsed_validated", city_estimate_status="not_identifiable_in_public_use_file",
                     available_geography="Census division/region; MSA categories; urban/rural categories",
                     evidence="Complete CSV headers plus codebook; no city, county, state or named CBSA identifier",
                     model_use="national age-specific travel context; never impute this as city observations") for city in cities]
    write_csv(folder / "city_coverage.csv", coverage, list(coverage[0]))
    result = dict(version="2022 public-use V2.1", tables=inventory, youth_persons=len(youth),
                  youth_trips=len(youth_trips), age_range=[14, 18], household_key_unique=True,
                  person_key_unique=True, person_household_foreign_keys=True, trip_person_foreign_keys=True,
                  person_weight="WTPERFIN", trip_weight="WTTRDFIN", household_weight="WTHHFIN",
                  design_stratum="STRATUMID", variance_method="Taylor linearization; user guide PDF page 33",
                  replicate_weights="not available for NextGen NHTS; explicitly stated on user guide PDF page 33",
                  age_filter_note="14-18 age subset; age alone does not establish public high-school enrollment",
                  city_estimates="not identifiable in this public-use version", status="validated")
    assert "STRATUMID" in persons[0]
    write_json(folder / "validation.json", result)
    print(json.dumps({key: result[key] for key in ["youth_persons", "youth_trips", "status"]}))


if __name__ == "__main__":
    main()
