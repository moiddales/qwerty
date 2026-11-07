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
seq 1 5 > big.txt; rm -f t2.jsonl t3.jsonl t4.jsonl t5.jsonl t6.jsonl t7.jsonl
check "small diff -> allow"                             ""                          "$(stop t1.jsonl)"
check "garbage input fails open"                        ""                          "$(echo nope | rg)"

# --- session_base.py (SessionStart) + review_gate against the session's start commit ---
sb() { python3 -I "$H/session_base.py"; }
base_sha="$(git rev-parse HEAD)"
echo '{"session_id":"s9"}' | sb
check "session_base records the start commit"           "$base_sha"                 "$(cat .claude/state/base-s9 2>/dev/null)"
git -c user.email=t@t -c user.name=t commit -q --allow-empty -m later
echo '{"session_id":"s9"}' | sb
check "resume keeps the original base"                  "$base_sha"                 "$(cat .claude/state/base-s9 2>/dev/null)"
seq 1 60 > feature.txt && git add feature.txt && git -c user.email=t@t -c user.name=t commit -q -m feature
stop9() { printf '{"session_id":"s9","transcript_path":"%s/%s","stop_hook_active":false}' "$T" "$1" | rg; }
check "edit -> commit -> stop still blocks"             '"decision": "block"'       "$(stop9 t1.jsonl)"
check "without a recorded base, a commit hides it"      ""                          "$(stop t1.jsonl)"
{ tool Bash '{"command":"cat > feature.txt <<EOF"}'; } > t5.jsonl
check "Bash heredoc edit, no verifier -> block"         '"decision": "block"'       "$(stop9 t5.jsonl)"
{ tool Bash '{"command":"npm test 2>&1 | tail -5"}'; tool Bash '{"command":"git diff HEAD"}'; } > t6.jsonl
check "read-only Bash only -> allow"                    ""                          "$(stop9 t6.jsonl)"
{ tool Bash '{"command":"sed -i s/1/2/ feature.txt"}'; tool Agent '{"subagent_type":"verifier"}'; } > t7.jsonl
check "Bash edit then verifier -> allow"                ""                          "$(stop9 t7.jsonl)"

# --- empty repository (no commits yet) ---
E="$T/empty" && mkdir -p "$E" && git -C "$E" init -q && seq 1 60 > "$E/a.txt"
echo '{"session_id":"e1"}' | CLAUDE_PROJECT_DIR="$E" python3 -I "$H/session_base.py"
check "empty repo -> base is the empty tree"            "4b825dc642cb6eb9a060e54bf8d69288fbee4904" "$(cat "$E/.claude/state/base-e1" 2>/dev/null)"
check "empty repo, untracked 60 lines -> block"         '"decision": "block"'       "$(printf '{"session_id":"e1","transcript_path":"%s/t1.jsonl"}' "$T" | CLAUDE_PROJECT_DIR="$E" python3 -I "$H/review_gate.py")"

echo "passed=$pass failed=$fail"
[ "$fail" -eq 0 ]
