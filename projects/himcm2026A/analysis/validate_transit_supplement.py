"""Stream GTFS critical tables; distinguish complete schedules, dates and gaps."""
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from datetime import date
from collect_supplement_sources import SUPPLEMENT, write_json

FOLDER = SUPPLEMENT / "transit"
DATES = [date(2026, 11, 18), date(2026, 11, 14), date(2026, 11, 15)]
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def table(package, members, name):
    with package.open(members[name]) as stream:
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))


def validate(path):
    result = dict(file=str(path.relative_to(FOLDER)), bytes=path.stat().st_size,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with zipfile.ZipFile(path) as package:
        members = {Path(info.filename).stem.lower(): info.filename for info in package.infolist()
                   if not info.is_dir() and info.filename.lower().endswith((".txt", ".csv"))}
        required = {"agency", "stops", "routes", "trips", "stop_times"}
        absent = sorted(required - set(members))
        result["missing_critical_tables"] = absent
        if absent or not ({"calendar", "calendar_dates"} & set(members)):
            result["status"] = "incomplete_schedule_tables"
            return result
        data = {name: list(table(package, members, name)) for name in
                ["agency", "stops", "routes", "trips", "calendar", "calendar_dates", "frequencies", "feed_info"] if name in members}
        stops = {row["stop_id"] for row in data["stops"]}
        routes = {row["route_id"] for row in data["routes"]}
        trips = {row["trip_id"]: row for row in data["trips"]}
        calendars = data.get("calendar", [])
        exceptions = data.get("calendar_dates", [])
        services = {row["service_id"] for row in calendars + exceptions}
        active = {}
        for day in DATES:
            key = day.strftime("%Y%m%d")
            current = {row["service_id"] for row in calendars if row[WEEKDAYS[day.weekday()]] == "1"
                       and row["start_date"] <= key <= row["end_date"]}
            for row in exceptions:
                if row["date"] == key:
                    if row["exception_type"] == "1":
                        current.add(row["service_id"])
                    elif row["exception_type"] == "2":
                        current.discard(row["service_id"])
            active[key] = current
        seen_trips = set()
        stop_time_count = bad_trip = bad_stop = missing_times = 0
        active_time_rows = {key: 0 for key in active}
        for row in table(package, members, "stop_times"):
            stop_time_count += 1
            trip = row["trip_id"]
            seen_trips.add(trip)
            if trip not in trips:
                bad_trip += 1
            if row["stop_id"] not in stops:
                bad_stop += 1
            if not row["arrival_time"] or not row["departure_time"]:
                missing_times += 1
            if trip in trips:
                for key, service_ids in active.items():
                    if trips[trip]["service_id"] in service_ids:
                        active_time_rows[key] += 1
        route_errors = sum(row["route_id"] not in routes for row in trips.values())
        service_errors = sum(row["service_id"] not in services for row in trips.values())
        frequency_rows = data.get("frequencies", [])
        frequency_errors = sum(row["trip_id"] not in trips for row in frequency_rows)
        result.update(table_rows={name: len(rows) for name, rows in data.items()}, stop_time_rows=stop_time_count,
                      agency_timezones=sorted({row["agency_timezone"] for row in data["agency"]}),
                      feed_info=data.get("feed_info", []),
                      trips_duplicate_ids=len(data["trips"]) - len(trips),
                      stops_duplicate_ids=len(data["stops"]) - len(stops),
                      stop_times_unknown_trip_rows=bad_trip, stop_times_unknown_stop_rows=bad_stop,
                      trips_unknown_route=route_errors, trips_unknown_service=service_errors,
                      trips_without_stop_times=len(set(trips) - seen_trips), missing_time_rows=missing_times,
                      frequency_rows=len(frequency_rows), frequency_unknown_trips=frequency_errors,
                      frequency_exact_times=sorted({row.get("exact_times", "") for row in frequency_rows}),
                      active_stop_time_rows=active_time_rows,
                      temporal_scope="2026 snapshot; do not assign these schedules to the 2024 base window",
                      frequency_handling="Retain headway and exact_times; template rows are not counted as literal departures",
                      missing_time_handling="Retained for interpolation at routing stage; never replace blanks by midnight",
                      round_trip_status="raw schedule inputs acquired; origin/destination/opening/eligibility routing still required")
        errors = bad_trip + bad_stop + route_errors + service_errors + frequency_errors
        result["status"] = "critical_tables_and_links_validated" if not errors and stop_time_count and all(data[name] for name in ["agency", "stops", "routes", "trips"]) else "schedule_quality_gap"
    return result


def main():
    registry = json.loads((FOLDER / "selected_feed_registry_local.json").read_text(encoding="utf-8"))
    out = FOLDER / "feed_validation"
    out.mkdir(exist_ok=True)
    for row in registry:
        feed = row["feed_id"]
        target = out / (feed + ".json")
        path = FOLDER / "raw_local/current_gtfs" / (feed + ".zip")
        if not path.exists():
            print(feed, "no complete download", flush=True)
            continue
        if target.exists() and json.loads(target.read_text(encoding="utf-8"))["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest():
            continue
        result = dict(feed_id=feed, city_id=row["city_id"], provider=row["provider"], **validate(path))
        write_json(target, result)
        print(feed, result["status"], result.get("stop_time_rows"), flush=True)


if __name__ == "__main__":
    main()
