"""Acquire official NHTS files and the NTM catalog; log local HTTP evidence."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import csv
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request

PROJECT = Path(__file__).resolve().parents[1]
SUPPLEMENT = PROJECT / "supplement_20261111"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch(url, path, log, source):
    """Keep successful bytes and failed HTTP responses distinct in an append-only log."""
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = dict(source=source, url=url, retrieved_at=datetime.now(timezone.utc).isoformat(),
                 channel="local Windows Python urllib HTTPS GET", path=str(path.relative_to(PROJECT)))
    request = urllib.request.Request(url, headers={"User-Agent": "HiMCM2026A-research/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read()
            entry.update(http_status=response.status, final_url=response.url,
                         content_type=response.headers.get("Content-Type"), bytes=len(body),
                         sha256=hashlib.sha256(body).hexdigest())
            path.write_bytes(body)
    except urllib.error.HTTPError as error:
        body = error.read()
        entry.update(http_status=error.code, content_type=error.headers.get("Content-Type"),
                     error=str(error), response_bytes=len(body),
                     response_sha256=hashlib.sha256(body).hexdigest(), classification="cause_unverified")
    except (urllib.error.URLError, TimeoutError) as error:
        entry.update(error=str(error), classification="cause_unverified")
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(source, path.name, entry.get("http_status"), entry.get("bytes"), flush=True)
    return entry


def nhts():
    folder = SUPPLEMENT / "nhts"
    log = folder / "http_requests.jsonl"
    base = "https://nhts.ornl.gov/media/2022/"
    targets = [
        ("download/csv.zip", "raw/nhts_2022_v2_1_csv.zip"),
        ("doc/codebook.pdf", "raw/codebook.pdf"),
        ("doc/2022 NextGen NHTS User's Guide V201_PubUse.pdf", "raw/users_guide_v2_1.pdf"),
        ("doc/2022 NextGen NHTS Weighting Memo.pdf", "raw/weighting_memo.pdf"),
        ("doc/2022 NextGen NHTS V2.1 Release Notes.pdf", "raw/release_notes_v2_1.pdf"),
        ("doc/2022 NextGen NHTS Derived Variables-PubUseV2.1.pdf", "raw/derived_variables_v2_1.pdf"),
    ]
    for suffix, filename in targets:
        fetch(base + urllib.parse.quote(suffix), folder / filename, log, "NHTS2022")


def ntm():
    folder = SUPPLEMENT / "transit"
    fetch("https://ntmcatalog.bts.gov/ntmdownloads", folder / "ntm_download_dates.json",
          folder / "http_requests.jsonl", "BTS_NTM")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", choices=["nhts", "ntm"])
    args = parser.parse_args()
    {"nhts": nhts, "ntm": ntm}[args.source]()
