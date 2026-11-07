#!/usr/bin/env python3
"""PostToolUseFailure (Bash): nudge the session when the same failure repeats.

Input fields per the hooks docs: tool_input.command, error ("Exit code N\n..."),
is_interrupt, session_id. Deterministic, offline, fails open: any error -> no output.
State: $CLAUDE_PROJECT_DIR/.claude/state/failures-<session>.json
"""
import hashlib, json, os, re, sys

def norm(text: str) -> str:
    text = text[-2000:]
    text = re.sub(r"0x[0-9a-fA-F]+", "<hex>", text)
    text = re.sub(r"\d+(\.\d+)?", "<n>", text)          # line numbers, timings
    text = re.sub(r"/[\w./-]*/(tmp|T)/[\w./-]+", "<tmp>", text)
    return re.sub(r"\s+", " ", text).strip()

def main() -> None:
    ev = json.load(sys.stdin)
    if ev.get("is_interrupt"):          # user/abort, not a real failure
        return
    cmd = (ev.get("tool_input") or {}).get("command", "")
    raw = ev.get("error") or ev.get("tool_response") or ""
    if not isinstance(raw, str):
        raw = json.dumps(raw)
    key = hashlib.sha1((cmd.split(" ")[0] + "|" + norm(raw)).encode()).hexdigest()[:16]

    root = os.environ.get("CLAUDE_PROJECT_DIR") or ev.get("cwd") or "."
    sdir = os.path.join(root, ".claude", "state")
    os.makedirs(sdir, exist_ok=True)
    sid = re.sub(r"[^\w-]", "", str(ev.get("session_id", "default")))[:64]
    path = os.path.join(sdir, f"failures-{sid}.json")
    try:
        state = json.load(open(path))
    except Exception:
        state = {}
    state[key] = state.get(key, 0) + 1
    json.dump(state, open(path, "w"))

    if state[key] >= 2:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUseFailure",
            "additionalContext": (
                f"Repeated failure #{state[key]} for the same error. Per CLAUDE.md: "
                "stop editing and get a root-cause opinion (advisor, or the verifier "
                "with .claude/plan.md) before trying another fix.")}}))

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
