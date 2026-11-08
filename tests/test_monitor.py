#!/usr/bin/env python3
"""Tests for .claude/monitor/team_monitor.py.  Run: python3 tests/test_monitor.py

Synthetic transcripts use the entry shapes observed in a real Claude Code
2.1.319 transcript; tests/fixtures/real-session.jsonl is a trimmed,
path-scrubbed copy of one real nested session.
"""
import importlib.util, json, os, pty, re, select, signal, subprocess, sys, tempfile, time
sys.dont_write_bytecode = True

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON = os.path.join(ROOT, ".claude", "monitor", "team_monitor.py")
spec = importlib.util.spec_from_file_location("team_monitor", MON)
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1; print(f"ok   - {name}")
    else:
        failed += 1; print(f"FAIL - {name}" + (f"\n       {detail}" if detail else ""))

# ---- tiny transcript builder (same shapes as the real transcript) ----------
class T:
    def __init__(self):
        self.e, self.s = [], 0
    def _ts(self):
        self.s += 1
        return f"2026-11-08T10:00:{self.s:02d}.000Z"
    def use(self, i, name, model="claude-sonnet-5-5", **inp):
        self.e.append({"type": "assistant", "timestamp": self._ts(), "message": {"model": model, "content": [
            {"type": "tool_use", "id": i, "name": name, "input": inp}]}}); return self
    def res(self, i, text, err=False, tur=None):
        d = {"type": "user", "timestamp": self._ts(), "message": {"content": [
            {"type": "tool_result", "tool_use_id": i, "content": text, "is_error": err}]}}
        if tur is not None: d["toolUseResult"] = tur
        self.e.append(d); return self
    def agent(self, i, sub, result=None, background=False, model="claude-haiku-5-5"):
        self.use(i, "Agent", subagent_type=sub, description=f"{sub} job")
        if background:
            return self.res(i, "Async agent launched", tur={"status": "async_launched", "isAsync": True, "resolvedModel": model})
        return self.res(i, result or "", tur={"status": "completed", "resolvedModel": model})
    def notify(self, i, result, carrier="user", status="completed"):
        body = f"<task-notification>\n<tool-use-id>{i}</tool-use-id>\n<status>{status}</status>\n<result>{result}</result>\n</task-notification>"
        if carrier == "user":
            self.e.append({"type": "user", "timestamp": self._ts(), "message": {"content": body}})
        elif carrier == "attachment":
            self.e.append({"type": "attachment", "timestamp": self._ts(), "attachment": {"type": "queued_command", "prompt": body}})
        else:
            self.e.append({"type": "queue-operation", "operation": "enqueue", "timestamp": self._ts(), "content": body})
        return self
    def advisor(self):
        self.e.append({"type": "assistant", "timestamp": self._ts(), "message": {"model": "claude-sonnet-5-5", "content": [
            {"type": "server_tool_use", "id": "srv", "name": "advisor", "input": {}}]}}); return self
    def gate(self):
        self.e.append({"type": "user", "isMeta": True, "timestamp": self._ts(), "message": {"content": "Stop hook feedback: 60 changed lines"}}); return self
    def bash(self, i, cmd, out="", err=False):
        return self.use(i, "Bash", command=cmd).res(i, out, err)
    def edit(self, i, path="src/a.py"):
        return self.use(i, "Edit", file_path=path).res(i, "ok")
    def view(self):
        return tm.derive(tm.load_state(None, self.e), ROOT)

OK = "VERDICT: CONFIRMED\nFINDINGS: none"
BAD = "VERDICT: REFUTED\nFINDINGS:\nP1 · a.py:3 · flipped default"

# ---- SHIP and its reasons ----------------------------------------------------
v = T().agent("p", "verifier", OK, model="claude-opus-5-5").edit("e").bash("t", "npm test", "48 passed").agent("v", "verifier", OK).view()
check("positive SHIP: plan review, edit, green tests, review after last edit", v["ship"] and v["why"] == "confirmed", v["why"])
check("WAKES counts plan + done checkpoints", v["wakes"] == 2, v["wakes"])
v = T().edit("e").agent("v", "verifier", OK).bash("w", "sed -i s/a/b/ src/a.py").view()
check("CONFIRMED then Bash sed -i edit -> SHIP off (edit after review)", not v["ship"] and v["why"] == "edit after review", v["why"])
v = T().edit("e").agent("v", "verifier", OK).bash("t", "npm test 2>&1 | tail -5", "FAIL src/a.test.js\nTests: 1 failed", err=False).view()
check("CONFIRMED then piped failing test (is_error false) -> tests red", not v["ship"] and v["why"] == "tests red", v["why"])
v = T().agent("v", "verifier", OK).view()
check("no edits -> 'no changes', SHIP off", not v["ship"] and v["why"] == "no changes", v["why"])
v = T().edit("e").view()
check("edits but no review -> needs review", not v["ship"] and v["why"] == "needs review", v["why"])
v = T().edit("e").agent("v", "verifier", BAD).view()
check("REFUTED -> CAUGHT 1, SHIP off", v["caught"] == 1 and not v["ship"] and v["why"] == "refuted", (v["caught"], v["why"]))
v = T().edit("e").use("v", "Agent", subagent_type="verifier", description="d").view()
check("verifier still running after last edit -> 'reviewing'", v["why"] == "reviewing" and v["verifier_running"], v["why"])

# ---- verdict parsing ------------------------------------------------------------
v = T().edit("e").agent("v", "verifier", "Output exactly:\nVERDICT: CONFIRMED | REFUTED | INCONCLUSIVE\nI could not run the tests.").view()
check("echoed template line is not a verdict", v["latest"] is None and not v["ship"], v["latest"])
v = T().edit("e").agent("v", "verifier", "**VERDICT: CONFIRMED**\nok").view()
check("markdown-bold verdict line parses", v["ship"], v["why"])
v = T().edit("e").agent("v", "verifier", background=True, model="claude-opus-5-5").notify("v", OK, "attachment").view()
check("background verdict via attachment notification", v["ship"] and v["verifier"] == 1, v["why"])

# ---- background Haiku agents: all three notification carriers, dedupe ----------
for carrier in ("user", "attachment", "queue"):
    v = T().agent("x", "Explore", background=True).view()
    check(f"background Explore with no notification -> running ({carrier})", v["cards"][1]["state"] == "running")
    v = T().agent("x", "Explore", background=True).notify("x", "src/a.py:1", carrier).view()
    check(f"notification via {carrier} -> search card done", v["cards"][1]["state"] == "done", v["cards"][1])
v = T().agent("x", "Explore", background=True).notify("x", "r", "queue").notify("x", "r", "attachment").notify("x", "r", "user").view()
check("same notification on three carriers counts once", v["cards"][1]["runs"] == 1 and len([l for l in v["log"] if "done" in l["what"]]) == 1)
v = T().agent("x", "callsites", background=True).notify("x", "boom", status="failed").view()
check("failed notification -> grep card failed", v["cards"][2]["state"] == "failed")
v = T().agent("x", "tests", "Tests: 2 failed, 40 passed").view()
check("tests agent that reports failures -> tests card failed", v["cards"][0]["state"] == "failed")

# ---- repeat failures, advisor, gate, test heuristics --------------------------
v = T().bash("a", "npm test", "Exit code 1\nFAIL a.test.js:12 (31ms)", True).bash("b", "npm test", "Exit code 1\nFAIL a.test.js:14 (40ms)", True).view()
check("same test failure twice -> checkpoint lit + tests badge", v["cp"][1]["on"] and v["cards"][0].get("badge", ("",))[0] == "same error ×2")
check("repeat not yet consulted", v["cp"][1]["sub"][0] == "not consulted yet")
t = T().bash("a", "python3 x.py", "Exit code 1\nboom 7", True).bash("b", "python3 x.py", "Exit code 1\nboom 9", True).advisor()
v = t.view()
check("non-test repeat -> lead box flag, advisor after it -> consulted", v["repeat_main"] and v["cp"][1]["sub"][0] == "consulted ✓" and v["advisor"] == 1)
v = T().bash("a", "npm test", "Exit code 1\nFAIL x", True).bash("b", "npm test", "Exit code 1\nTypeError y", True).view()
check("different failures -> no repeat", not v["cp"][1]["on"])
v = T().gate().view()
check("stop-hook block appears as a gate log line", v["gates"] == 1 and v["log"][-1]["lane"] == "gate")
v = T().bash("t", "pytest -q", "12 passed; test_fails_open ok; 0 failed").view()
check("passing output with 'fail' words counts as pass", v["tests_pass"] == 1 and v["tests_fail"] == 0)
v = T().bash("t", "bash tests/test_hooks.sh", "ok - a\npassed=21 failed=0").view()
check("'passed=21 failed=0' is a pass (caught by a live verifier run)", v["tests_pass"] == 1 and v["tests_fail"] == 0)
for out in ("Tests:       1 failed, 40 passed", "== 2 failed, 10 passed in 0.3s =="):
    v = T().bash("t", "npm test", out).view()
    check(f"summary {out.strip()[:22]!r} is a fail", v["tests_fail"] == 1)
v = T().bash("t", "bash tests/test_hooks.sh", "ok - a\nFAIL - big diff\ndone").view()
check("line-start FAIL marker counts as fail", v["tests_fail"] == 1)
v = T().bash("t", "git diff HEAD", "").view()
check("non-test command is not a test run", v["tests_pass"] + v["tests_fail"] == 0)

# ---- regressions from the diff review -------------------------------------------
v = T().edit("e").agent("v", "verifier", OK).bash("t", "python3 tests/test_monitor.py", "Exit code 1\nFAIL - x\npassed=40 failed=1", True).view()
check("this repo's own monitor suite failing -> tests red", not v["ship"] and v["why"] == "tests red", v["why"])
hooks_out = subprocess.run(["bash", os.path.join(ROOT, "tests", "test_hooks.sh")], capture_output=True, text=True).stdout
mon_out = ("ok   - summary 'Tests:       1 failed,' is a fail\nok   - summary '== 2 failed, 10 passed' is a fail\n"
           "ok   - line-start FAIL marker counts as fail\nok   - real fixture: advisor 1, same error ×2\npassed=41 failed=0")
v = T().edit("e").agent("v", "verifier", OK).bash("t", "python3 tests/test_monitor.py && bash tests/test_hooks.sh", mon_out + "\n" + hooks_out).view()
check("all-green chained run of both suites (real hooks output) counts as pass", v["ship"] and v["tests_pass"] == 1, (v["why"], hooks_out[-60:]))
v = T().edit("e").bash("t", "npm test", "Exit code 1\nFAIL a", True).agent("v", "verifier", OK).view()
check("a red run before the verdict does not block SHIP", v["ship"], v["why"])
for cmd in ("uv run pytest -q", "npx playwright test", "make -C build test", "tox -e py313", "python3 -m pytest", "go test ./..."):
    v = T().bash("t", cmd, "Exit code 1\nboom", True).view()
    check(f"test runner detected: {cmd}", v["tests_fail"] == 1)
v = T().bash("t", "npm test", "warning: 3 errors suppressed\nFound 2 errors in docs\n1 error generated\nTests: 9 passed").view()
check("'N errors' noise in a zero-exit run is not a test failure", v["tests_pass"] == 1 and v["tests_fail"] == 0)
v = T().bash("a", "npm run dev", "[Request interrupted by user for tool use]", True).bash("b", "npm run dev", "[Request interrupted by user for tool use]", True).view()
check("two interrupts are not 'same error ×2' (matches the hook)", not v["cp"][1]["on"])

# ---- robustness + rendering -----------------------------------------------------
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "t.jsonl")
    t = T().edit("e").agent("v", "verifier", OK)
    with open(p, "w") as fh:
        fh.write("not json\n")
        for e in t.e:
            fh.write(json.dumps(e) + "\n")
        fh.write('{"type": "assistant", "message": {"content": [{"type": "tool_u')  # partial line
    st = tm.load_state(p)
    check("garbage and partial lines are skipped", st is not None and len(st.edits) == 1)
    out = subprocess.run([sys.executable, "-I", MON, "--once", "--no-color", "--project", d, "--transcript", os.path.join(d, "missing.jsonl")],
                         capture_output=True, text=True)
    check("missing transcript -> waiting frame, exit 0", out.returncode == 0 and "waiting for a Claude Code session" in out.stdout, out.stderr[-300:])
    widths = {len(l) for l in out.stdout.splitlines()}
    check("waiting frame is 100 columns", widths == {100}, widths)

def frame_lines(*args):
    r = subprocess.run([sys.executable, "-I", MON, "--once", "--project", ROOT, *args], capture_output=True, text=True)
    return r, [re.sub(r"\033\[[0-9;]*m", "", l) for l in r.stdout.splitlines()]

real = os.path.join(ROOT, "tests", "fixtures", "real-session.jsonl")
r, lines = frame_lines("--transcript", real)
text = "\n".join(lines)
check("real fixture renders, every ANSI-stripped line is 100 columns", r.returncode == 0 and {len(l) for l in lines} == {100}, r.stderr[-300:])
check("real fixture: Explore (search) done on haiku 5.5", re.search(r"haiku 5\.5 .*│", text) and "done ✓" in text)
check("real fixture: verifier verdict CONFIRMED parsed from notification", "VERDICT: CONFIRMED" in text)
check("real fixture: advisor 1, same error ×2, gate line, WAKES 2/3",
      "advisor 1" in text and "same error ×2" in text and "stop blocked" in text and "2/3" in text)
r, lines = frame_lines("--demo")
check("demo frame is labelled DEMO and 100 columns", "● DEMO" in lines[0] and {len(l) for l in lines} == {100})

# ---- live loop: alt screen in, restored on Ctrl-C --------------------------------
pid, fd = pty.fork()
if pid == 0:
    os.environ["COLUMNS"] = "110"
    os.execv(sys.executable, [sys.executable, "-I", MON, "--demo", "--interval", "0.2", "--project", ROOT])
buf, end = b"", time.time() + 2.5
while time.time() < end:
    if select.select([fd], [], [], 0.1)[0]:
        try:
            buf += os.read(fd, 65536)
        except OSError:
            break
os.kill(pid, signal.SIGINT)
end = time.time() + 3
while time.time() < end:
    if select.select([fd], [], [], 0.1)[0]:
        try:
            chunk = os.read(fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
_, status = os.waitpid(pid, 0)
check("live loop enters alt screen and draws", b"\x1b[?1049h" in buf and b"OPUS REVIEWS" in buf)
check("Ctrl-C restores the screen and exits 0", b"\x1b[?1049l" in buf and os.WEXITSTATUS(status) == 0, status)

print(f"passed={passed} failed={failed}")
sys.exit(1 if failed else 0)
