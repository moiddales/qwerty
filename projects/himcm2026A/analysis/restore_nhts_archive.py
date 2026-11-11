"""Restore the official NHTS ZIP from exact-byte Git parts."""
from pathlib import Path
import base64
import hashlib
import json
import zipfile

folder = Path(__file__).resolve().parents[1] / "supplement_20261111/nhts"
manifest = json.loads((folder / "archive_manifest.json").read_text(encoding="utf-8"))
archive = folder / manifest["archive_path"]
archive.parent.mkdir(parents=True, exist_ok=True)
with archive.open("wb") as stream:
    for part in manifest["parts"]:
        encoded = (folder / part["path"]).read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == part["sha256"]
        stream.write(base64.b64decode(encoded))
assert archive.stat().st_size == manifest["archive_bytes"]
assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["archive_sha256"]
with zipfile.ZipFile(archive) as package:
    assert package.testzip() is None
print("Verified restored NHTS ZIP:", archive)
