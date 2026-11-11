"""Try the catalog's explicit public mirror after recorded operator download failures."""
import json
from concurrent.futures import ThreadPoolExecutor
from collect_supplement_sources import SUPPLEMENT, fetch

folder = SUPPLEMENT / "transit"
registry = json.loads((folder / "selected_feed_registry_local.json").read_text(encoding="utf-8"))
missing = [row for row in registry if not (folder / "raw_local/current_gtfs" / (row["feed_id"] + ".zip")).exists()]


def acquire(row):
    feed = row["feed_id"]
    return fetch(row["mirror_url"], folder / "raw_local/current_gtfs" / (feed + ".zip"),
                 folder / "feed_logs" / (feed + ".jsonl"), "MobilityData_explicit_mirror_after_recorded_direct_failure")


with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(acquire, missing))
print("Explicit mirror attempts:", len(results), flush=True)
