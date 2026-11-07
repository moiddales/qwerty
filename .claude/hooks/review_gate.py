#!/usr/bin/env python3
"""Stop hook: block "done" once if a non-trivial diff has no verifier pass after the last edit.

- Non-trivial = changed lines (tracked + untracked) >= REVIEW_GATE_MIN_LINES (default 40),
  measured against the commit the session started on (written by session_base.py), so
  committing before stopping does not hide the changes. Falls back to HEAD.
- Edits = Edit/Write/MultiEdit/NotebookEdit tool calls, plus Bash commands that look
  like file writes (sed -i, redirects, tee, heredocs, mv/cp, git apply, ...).
- Blocks at most once per stop (respects stop_hook_active), so it can never trap a session.
- Deterministic, offline, fails open.
- Reads tool_use blocks from transcript_path. The docs note the transcript can lag the
  live turn; worst case is one extra "please verify" block, never a trapped session.
"""
import json, os, re, subprocess, sys

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
AGENT_TOOLS = {"Agent", "Task"}
BASH_WRITE = re.compile(
    r"(\bsed\s+(-\w*\s+)*-i|(^|[^<>&0-9])>{1,2}\s*(?!&|/dev/null)[\w./~\"'$-]|\btee\b|<<-?\s*['\"]?\w+"
    r"|\b(mv|cp|rm|truncate|patch)\s|\bgit\s+(apply|checkout\s+--|restore|am)\b"
    r"|open\([^)]*['\"][wa]b?['\"]|write_text\(|writeFileSync\()")

def base_ref(cwd: str, session_id: str) -> str:
    sid = re.sub(r"[^\w-]", "", str(session_id or "default"))[:64]
    try:
        return open(os.path.join(cwd, ".claude", "state", f"base-{sid}")).read().strip() or "HEAD"
    except Exception:
        return "HEAD"

def changed_lines(cwd: str, base: str) -> int:
    def run(*a):
        return subprocess.run(a, cwd=cwd, capture_output=True, text=True, timeout=5).stdout
    total = 0
    for line in run("git", "diff", base, "--numstat").splitlines():
        a, d, *_ = line.split("\t")
        total += int(a) if a.isdigit() else 0
        total += int(d) if d.isdigit() else 0
    for f in run("git", "ls-files", "--others", "--exclude-standard").splitlines():
        if f.startswith(".claude/"):
            continue
        try:
            total += sum(1 for _ in open(os.path.join(cwd, f), errors="ignore"))
        except Exception:
            pass
    return total

def last_positions(transcript: str):
    last_edit = last_verify = -1
    with open(transcript) as fh:
        for i, line in enumerate(fh):
            try:
                msg = json.loads(line).get("message") or {}
            except Exception:
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                inp = block.get("input") or {}
                if name in EDIT_TOOLS or (name == "Bash" and BASH_WRITE.search(inp.get("command", ""))):
                    last_edit = i
                elif name in AGENT_TOOLS and inp.get("subagent_type") == "verifier":
                    last_verify = i
    return last_edit, last_verify

def main() -> None:
    ev = json.load(sys.stdin)
    if ev.get("stop_hook_active"):
        return
    cwd = os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or "."
    last_edit, last_verify = last_positions(ev["transcript_path"])
    if last_edit < 0 or last_verify > last_edit:
        return
    n = changed_lines(cwd, base_ref(cwd, ev.get("session_id")))
    if n < int(os.environ.get("REVIEW_GATE_MIN_LINES", "40")):
        return
    print(json.dumps({"decision": "block", "reason": (
        f"{n} changed lines and no verifier pass since the last edit. Per CLAUDE.md's done gate: "
        "run the plan's checks, call the verifier with .claude/plan.md, then report. "
        "If this is not meant to be done yet, say so and stop.")}))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
