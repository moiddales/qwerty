#!/usr/bin/env bash
# Replays simulated hook inputs against both hooks in a throwaway git repo.
# Usage: bash tests/test_hooks.sh      (needs bash, git, python3)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
H="$ROOT/.claude/hooks"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
cd "$T" && git init -q && git -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
export CLAUDE_PROJECT_DIR="$T"
pass=0; fail=0
check() { # name, expected substring ("" = expect no output), actual
  local ok=0
  if [ -z "$2" ]; then [ -z "$3" ] && ok=1; else [[ "$3" == *"$2"* ]] && ok=1; fi
  if [ "$ok" -eq 1 ]; then
    pass=$((pass+1)); echo "ok   - $1"
  else
    fail=$((fail+1)); echo "FAIL - $1"; echo "       expected: ${2:-<no output>}"; echo "       got:      ${3:-<no output>}"
  fi
}
rf() { python3 -I "$H/repeat_failure.py"; }
rg() { python3 -I "$H/review_gate.py"; }
tool() { printf '{"message":{"role":"assistant","content":[{"type":"tool_use","name":"%s","input":%s}]}}\n' "$1" "${2:-{\}}"; }

# --- repeat_failure.py (PostToolUseFailure) ---
f1='{"session_id":"s1","hook_event_name":"PostToolUseFailure","tool_name":"Bash","tool_input":{"command":"npm test"},"error":"Exit code 1\nFAIL src/a.test.js:12 expected 3 got 4 (34ms)","is_interrupt":false}'
f2='{"session_id":"s1","hook_event_name":"PostToolUseFailure","tool_name":"Bash","tool_input":{"command":"npm test"},"error":"Exit code 1\nFAIL src/a.test.js:14 expected 3 got 4 (51ms)","is_interrupt":false}'
f3='{"session_id":"s1","hook_event_name":"PostToolUseFailure","tool_name":"Bash","tool_input":{"command":"npm test"},"error":"Exit code 1\nTypeError: x is undefined","is_interrupt":false}'
f4='{"session_id":"s2","tool_input":{"command":"npm test"},"error":"Exit code 130","is_interrupt":true}'
check "first failure is silent"                         ""                          "$(echo "$f1" | rf)"
check "same failure again (new line/timing) nudges"     "Repeated failure #2"       "$(echo "$f2" | rf)"
check "different failure is silent"                     ""                          "$(echo "$f3" | rf)"
check "interrupts are ignored"                          ""                          "$( (echo "$f4"; ) | rf; echo "$f4" | rf)"
check "garbage input fails open"                        ""                          "$(echo nope | rf)"

# --- review_gate.py (Stop) ---
seq 1 60 > big.txt
{ tool Write; } > t1.jsonl
{ tool Write; tool Agent '{"subagent_type":"verifier"}'; } > t2.jsonl
{ tool Write; tool Agent '{"subagent_type":"verifier"}'; tool Edit; } > t3.jsonl
{ tool Agent '{"subagent_type":"Explore"}'; } > t4.jsonl
stop() { printf '{"transcript_path":"%s/%s","stop_hook_active":%s}' "$T" "$1" "${2:-false}" | rg; }
check "big diff, no verifier -> block"                  '"decision": "block"'       "$(stop t1.jsonl)"
check "verifier after last edit -> allow"               ""                          "$(stop t2.jsonl)"
check "edit after verifier -> block"                    '"decision": "block"'       "$(stop t3.jsonl)"
check "stop_hook_active -> never block twice"           ""                          "$(stop t3.jsonl true)"
check "no edits this session -> allow"                  ""                          "$(stop t4.jsonl)"
seq 1 5 > big.txt; rm -f t2.jsonl t3.jsonl t4.jsonl
check "small diff -> allow"                             ""                          "$(stop t1.jsonl)"
check "garbage input fails open"                        ""                          "$(echo nope | rg)"

echo "passed=$pass failed=$fail"
[ "$fail" -eq 0 ]
