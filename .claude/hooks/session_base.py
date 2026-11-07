#!/usr/bin/env python3
"""SessionStart: remember the commit this session started from.

review_gate.py diffs against it, so committing before stopping doesn't hide
the session's changes. Written once per session_id; a resume keeps the
original base. Deterministic, offline, fails open.
"""
import json, os, re, subprocess, sys

EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

def main() -> None:
    ev = json.load(sys.stdin)
    root = os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or "."
    sid = re.sub(r"[^\w-]", "", str(ev.get("session_id", "default")))[:64]
    sdir = os.path.join(root, ".claude", "state")
    path = os.path.join(sdir, f"base-{sid}")
    if os.path.exists(path):
        return
    head = subprocess.run(["git", "rev-parse", "--verify", "-q", "HEAD"], cwd=root,
                          capture_output=True, text=True, timeout=5).stdout.strip()
    os.makedirs(sdir, exist_ok=True)
    with open(path, "w") as fh:
        fh.write(head or EMPTY_TREE)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
