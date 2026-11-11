"""Acquire current operator GTFS from the observed MobilityData CC0 catalog."""
from concurrent.futures import ThreadPoolExecutor
import csv
import json
from collect_supplement_sources import PROJECT, SUPPLEMENT, fetch, write_json

FOLDER = SUPPLEMENT / "transit"
# Explicit operator/mode mapping, not a claim of exhaustive city service coverage.
CITY_FEEDS = {
    "3651000": ["mdb-510", "mdb-512", "mdb-513", "mdb-514", "mdb-516", "mdb-520", "mdb-528"],
    "0644000": ["mdb-29", "mdb-30"], "1714000": ["mdb-389"], "4835000": ["mdb-2060"],
    "0455000": ["mdb-147"], "4260000": ["mdb-502", "mdb-503"], "4865000": ["tld-217"],
    "0666000": ["mdb-13"], "4819000": ["mdb-152"], "4827000": ["mdb-2890"],
    "1235000": ["tld-764"], "4805000": ["mdb-150"], "0668000": ["mdb-57"],
    "3712000": ["mdb-2265"], "3918000": ["mdb-404"], "1836003": ["ntd-50050"],
    "0667000": ["mdb-2886"], "5363000": ["mdb-1330", "mdb-268"], "0820000": ["mdb-178"],
    "4752006": ["mdb-360"], "4055000": ["mdb-2062"], "1150000": ["mdb-1846", "mdb-1847"],
    "4824000": ["mdb-148"], "3240000": ["mdb-2351"], "2507000": ["mdb-437"],
}


def main():
    with (FOLDER / "mobility_database_feeds_v2.csv").open(encoding="utf-8-sig") as stream:
        catalog = {row["id"]: row for row in csv.DictReader(stream)}
    selected = []
    for city, feeds in CITY_FEEDS.items():
        for feed in feeds:
            row = catalog[feed]
            assert row["data_type"] == "gtfs" and row["location.country_code"] == "US"
            selected.append(dict(city_id=city, feed_id=feed, provider=row["provider"], mode_name=row["name"],
                                 catalog_status=row["status"], direct_url=row["urls.direct_download"],
                                 mirror_url=row["urls.latest"], license_url=row["urls.license"],
                                 catalog_id=feed, coverage="named operators/modes; additional city providers pending"))
    write_json(FOLDER / "selected_feed_registry_local.json", selected)

    def acquire(row):
        feed = row["feed_id"]
        log = FOLDER / "feed_logs" / (feed + ".jsonl")
        target = FOLDER / "raw_local/current_gtfs" / (feed + ".zip")
        if target.exists():
            return dict(feed_id=feed, acquisition_status="previous_saved_download_pending_validation",
                        path=str(target.relative_to(PROJECT)))
        direct = row["direct_url"]
        # This catalog entry embeds a public service key. Use its documented mirror;
        # do not copy a key-bearing URL into published request logs.
        if "apikey=" in direct.lower():
            url, channel = row["mirror_url"], "catalog_mirror_key_bearing_direct_not_requested"
        else:
            url, channel = direct, "operator_direct"
        entry = fetch(url, target, log, channel)
        return dict(feed_id=feed, attempted_channel=channel, **entry)

    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(acquire, selected))
    write_json(FOLDER / "acquisition_results_local.json", results)
    print("Attempted", len(results), "feeds for", len(CITY_FEEDS), "cities", flush=True)


if __name__ == "__main__":
    main()
