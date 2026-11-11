"""Document a second, native-curl transport for observed Python TLS failures.

The original requests failures remain in access_evidence.json. This is an
explicit alternate-channel check, not an automatic replacement or retry loop.
"""
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo

import fitz
from lxml import html

from collect_youth_services import ROOT, write_csv

IDS = {"indianapolis_activity", "indianapolis_mental_payment", "jacksonville_mental_hours", "lasvegas_mental"}


def check(source):
    path = ROOT / "raw_local" / (source["source_id"] + "_curl.body")
    command = ["curl.exe", "--location", "--silent", "--show-error", "--max-time", "40", "--output", str(path), "--write-out", "%{json}", source["url"]]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    meta = json.loads(result.stdout)
    row = dict(source_id=source["source_id"], url=source["url"], checked_at=datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"), environment="user_local_windows_native_curl", request_method="GET", http_status=meta["http_code"], curl_exit_code=result.returncode, final_url=meta["url_effective"], content_type=meta.get("content_type", ""), downloaded_bytes=path.stat().st_size if path.exists() else "", raw_local_path=path.relative_to(ROOT).as_posix() if path.exists() else "", parsed_local_path="", parse_status="", marker_status="", error=result.stderr.strip(), source_republication="original excluded; short facts and URL only")
    if result.returncode == 0 and row["http_status"] == 200:
        blob = path.read_bytes()
        if blob.startswith(b"%PDF"):
            with fitz.open(stream=blob, filetype="pdf") as doc:
                content = "\n".join(page.get_text() for page in doc)
            row["parse_status"] = "pdf_text_parsed"
        else:
            tree = html.fromstring(blob)
            for element in tree.xpath("//script|//style|//noscript"):
                element.drop_tree()
            content = tree.text_content()
            row["parse_status"] = "html_text_parsed"
        parsed_path = ROOT / "raw_local" / (source["source_id"] + "_curl.txt")
        parsed_path.write_text(content, encoding="utf-8")
        row["parsed_local_path"] = parsed_path.relative_to(ROOT).as_posix()
        row["marker_status"] = "present" if " ".join(source["content_marker"].lower().split()) in " ".join(content.lower().split()) else "not_found_review_required"
    return row


if __name__ == "__main__":
    sources = [s for p in ROOT.glob("sources*.json") for s in json.loads(p.read_text(encoding="utf-8")) if s["source_id"] in IDS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(check, sources))
    (ROOT / "curl_access_evidence.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(ROOT / "curl_access_evidence.csv", rows, list(rows[0]))
    print(json.dumps(rows, ensure_ascii=True, indent=2))
