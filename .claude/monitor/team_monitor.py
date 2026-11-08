#!/usr/bin/env python3
"""team_monitor: a terminal "model team" dashboard for this repo's Claude Code setup.

Run it in its own terminal window or tmux pane next to a Claude Code session:

    python3 .claude/monitor/team_monitor.py            # live, follows the newest session
    python3 .claude/monitor/team_monitor.py --demo     # scripted sample session (labelled DEMO)

Everything shown in live mode is derived from the session transcript (JSONL)
that Claude Code writes; nothing is simulated and no model tokens are used.
Stdlib only. Read-only: it never writes to the project or the transcript.
"""
from __future__ import annotations

import argparse
import glob
import html
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone

W = 100                      # frame width in columns
LEFT, GAP, RIGHT = 30, 2, 68 # left Opus card | right column
HERE = os.path.dirname(os.path.abspath(__file__))
HOOKS = os.path.normpath(os.path.join(HERE, "..", "hooks"))

# ---------------------------------------------------------------- shared rules
# Edit and repeat-failure definitions come from the hooks, so the monitor never
# disagrees with what review_gate.py / repeat_failure.py enforce.

def _load_hook(name: str):
    sys.dont_write_bytecode = True  # read-only: don't leave __pycache__ in .claude/hooks
    try:
        spec = importlib.util.spec_from_file_location(f"_hook_{name}", os.path.join(HOOKS, f"{name}.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # module bodies only define names; main() is guarded
        return mod
    except Exception:
        return None

_rg, _rf = _load_hook("review_gate"), _load_hook("repeat_failure")
EDIT_TOOLS = getattr(_rg, "EDIT_TOOLS", {"Edit", "Write", "MultiEdit", "NotebookEdit"})
BASH_WRITE = getattr(_rg, "BASH_WRITE", re.compile(r"\bsed\s+-i|>{1,2}\s*\w|\btee\b|<<"))
norm = getattr(_rf, "norm", lambda s: re.sub(r"\d+", "<n>", s[-2000:]).strip())

AGENT_TOOLS = {"Agent", "Task"}
CARDS = [("tests", "tests", "runs tests"), ("Explore", "search", "maps the repo"), ("callsites", "grep", "finds call sites")]

# Test runner as a command word (also after &&, ;, |, or a leading VAR=x).
TEST_RE = re.compile(
    r"(?:^|&&|;|\|\|?|\()\s*(?:\w+=\S*\s+)*(?:(?:uv|poetry|pdm|hatch)\s+run\s+)?(?:"
    r"(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test\b|npx\s+(?:jest|vitest|mocha|playwright\s+test)\b"
    r"|(?:jest|vitest|mocha|pytest|py\.test|tox|nox)\b"
    r"|python3?\s+(?:-\w+\s+)*(?:-m\s+(?:pytest|unittest)\b|\S*test\S*\.py\b)"
    r"|go\s+test\b|cargo\s+test\b|make\s+(?:-C\s+\S+\s+)?(?:test|check)\b"
    r"|(?:bash|sh)\s+\S*test\S*\.sh\b|\./\S*test\S*\.sh\b)")
# Failure markers for runs that exited 0 (e.g. piped into tail). Anchored to
# line starts / summary lines so test *names* that mention "1 failed" or
# "FAIL" mid-line do not count. A non-zero exit is always a failure.
FAIL_RE = re.compile(
    r"(?m)^\s*(?:---\s*)?FAIL(?:ED)?\b"                       # jest/vitest "FAIL x", go "--- FAIL", pytest "FAILED x"
    r"|test result: FAILED"                                     # cargo
    r"|^[\s=]*(?:Tests?:\s*|Test Suites:\s*)?[1-9]\d*\s+(?:failed|failing)\b"  # jest/pytest/mocha summaries
    r"|^[\s=]*\d+\s+passed,\s*[1-9]\d*\s+failed\b"
    r"|(?<![\w'\"])failed=[1-9]"                              # this repo's own suites
    r"|^Traceback \(most recent call last\)|^npm ERR!")
VERDICT_RE = re.compile(r"^[\s*_`>]*VERDICT:[\s*_`]*(CONFIRMED|REFUTED|INCONCLUSIVE)[\s*_`.]*$", re.M)
TAG_RE = {k: re.compile(rf"<{k}>(.*?)</{k}>", re.S) for k in ("tool-use-id", "status", "result")}

# ---------------------------------------------------------------- transcript -> state

def pretty_model(m: str | None) -> str | None:
    if not m:
        return None
    m = m.replace("[1m]", "")
    hit = re.match(r"claude-(fable|opus|sonnet|haiku)-(\d+)(?:-(\d+))?", m)
    if hit:
        return f"{hit.group(1)} {hit.group(2)}" + (f".{hit.group(3)}" if hit.group(3) else "")
    return m


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def _ts(entry) -> float | None:
    raw = entry.get("timestamp")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def agent_models(project: str) -> dict:
    """model: field of each .claude/agents/*.md (fallback when resolvedModel is absent)."""
    out = {}
    for f in glob.glob(os.path.join(project, ".claude", "agents", "*.md")):
        try:
            head = open(f, encoding="utf-8").read(2000)
            name = re.search(r"^name:\s*(\S+)", head, re.M)
            model = re.search(r"^model:\s*(\S+)", head, re.M)
            if name and model:
                out[name.group(1)] = model.group(1)
        except Exception:
            pass
    return out


def settings_models(project: str) -> tuple[str | None, str | None]:
    try:
        s = json.load(open(os.path.join(project, ".claude", "settings.json")))
        return s.get("model"), s.get("advisorModel")
    except Exception:
        return None, None


class State:
    def __init__(self):
        self.seq = 0
        self.main_model = None
        self.turns = 0
        self.bash = 0
        self.edits: list[dict] = []
        self.tests: list[dict] = []      # {seq, ts, ok, via}
        self.fail_keys: dict[str, int] = {}
        self.repeat: dict | None = None  # first time any key hit 2
        self.advisor: list[dict] = []
        self.agents: dict[str, dict] = {}  # tool_use_id -> agent run
        self.gates: list[dict] = []
        self.log: list[dict] = []
        self.cost = None
        self.model_cost: dict[str, float] = {}
        self.now_doing = ""
        self.last_ts = None
        self.pending: dict[str, dict] = {}  # tool_use_id -> {"name", "input"}

    # -- helpers
    def _log(self, ts, who, what, lane, color=None):
        self.log.append({"ts": ts, "who": who, "what": what, "lane": lane, "color": color})

    def _finish_agent(self, tid, ts, status, text):
        a = self.agents.get(tid)
        if not a or a["end_seq"] is not None:
            return
        self.seq += 1
        a["end_seq"], a["end_ts"] = self.seq, ts
        a["status"] = "done" if status == "completed" else "failed"
        if a["type"] == "tests" and FAIL_RE.search(text or ""):
            a["status"] = "failed"  # the run finished, but the tests it ran are red
        v = VERDICT_RE.search(text or "")
        if v:
            a["verdict"] = v.group(1)
        who = pretty_model(a["model"]) or a["type"]
        if a["type"] == "verifier":
            verdict = a["verdict"] or "no verdict"
            color = {"CONFIRMED": "green", "REFUTED": "red"}.get(a["verdict"], "yellow")
            self._log(ts, who, f"verifier · VERDICT {verdict}", "review", color)
        else:
            self._log(ts, who, f"{a['label']} · {'done' if a['status'] == 'done' else 'failed'}", "swarm",
                      "green" if a["status"] == "done" else "red")

    # -- entry handlers
    def feed(self, e: dict):
        if not isinstance(e, dict) or e.get("isSidechain"):
            return
        t = e.get("type")
        ts = _ts(e) or self.last_ts
        if ts:
            self.last_ts = ts
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        content = msg.get("content")

        if t == "assistant":
            if msg.get("model") and not msg["model"].startswith("<"):
                self.main_model = msg["model"]
            for b in content if isinstance(content, list) else []:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "tool_use":
                    self._tool_use(b, ts)
                elif bt == "text" and b.get("text", "").strip():
                    self.now_doing = "replying"
                elif bt == "server_tool_use" and b.get("name") == "advisor":
                    self.seq += 1
                    self.advisor.append({"seq": self.seq, "ts": ts})
                    self._log(ts, "advisor", "consulted · reads full session", "review", "purple")
        elif t == "user":
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        self._tool_result(b, e.get("toolUseResult"), ts)
            elif isinstance(content, str):
                if content.lstrip().startswith("<task-notification>"):
                    self._notification(content, ts)
                elif e.get("isMeta") and content.startswith("Stop hook feedback:"):
                    self.seq += 1
                    self.gates.append({"seq": self.seq, "ts": ts})
                    self._log(ts, "gate", "stop blocked · review required", "gate", "yellow")
                elif not e.get("isMeta") and not content.startswith("<"):
                    self.turns += 1
        elif t == "queue-operation":
            body = e.get("content")
            if isinstance(body, str) and "<task-notification>" in body:
                self._notification(body, ts)
        elif t == "attachment":
            a = e.get("attachment") or {}
            if a.get("type") == "queued_command" and "<task-notification>" in str(a.get("prompt", "")):
                self._notification(str(a["prompt"]), ts)
        elif t == "cost-state":
            self.cost = e.get("totalCostUSD", self.cost)
            for model, u in (e.get("modelUsage") or {}).items():
                if isinstance(u, dict) and "costUSD" in u:
                    self.model_cost[model] = u["costUSD"]

    def _tool_use(self, b, ts):
        name, inp, tid = b.get("name"), b.get("input") or {}, b.get("id", "")
        self.pending[tid] = {"name": name, "input": inp}
        if name in AGENT_TOOLS:
            sub = inp.get("subagent_type") or "general-purpose"
            label = {c[0]: c[1] for c in CARDS}.get(sub, sub)
            self.seq += 1
            self.agents[tid] = {"type": sub, "label": label, "desc": inp.get("description", ""),
                                "start_seq": self.seq, "start_ts": ts, "end_seq": None, "end_ts": None,
                                "status": "running", "verdict": None, "model": None}
            lane = "review" if sub == "verifier" else "swarm"
            self._log(ts, sub, f"{label} · {inp.get('description', '')}".rstrip(" ·"), lane)
            self.now_doing = f"delegating · {sub}"
        elif name == "Bash":
            self.bash += 1
            cmd = inp.get("command", "")
            self.now_doing = "Bash " + cmd.splitlines()[0][:60] if cmd else "Bash"
            if BASH_WRITE.search(cmd):
                self._edit(ts, "bash write")
        elif name in EDIT_TOOLS:
            path = inp.get("file_path") or inp.get("notebook_path") or ""
            self.now_doing = f"{name} {os.path.basename(path)}"
            self._edit(ts, os.path.basename(path) or name)

    def _edit(self, ts, what):
        self.seq += 1
        self.edits.append({"seq": self.seq, "ts": ts})
        self._log(ts, "main", f"edit · {what}", "lead")

    def _tool_result(self, b, tur, ts):
        tid = b.get("tool_use_id", "")
        p = self.pending.get(tid)
        text = _text(b.get("content"))
        if tid in self.agents:
            a = self.agents[tid]
            if isinstance(tur, dict):
                a["model"] = tur.get("resolvedModel") or a["model"]
                if tur.get("status") in ("async_launched",) or tur.get("isAsync"):
                    return  # background run: completion arrives as a task-notification
            if b.get("is_error"):
                self._finish_agent(tid, ts, "failed", text)
            else:
                self._finish_agent(tid, ts, "completed", text)
            return
        if not p or p["name"] != "Bash":
            return
        cmd = p["input"].get("command", "")
        failed = bool(b.get("is_error"))
        if TEST_RE.search(cmd):
            ok = not failed and not FAIL_RE.search(text)
            self.seq += 1
            self.tests.append({"seq": self.seq, "ts": ts, "ok": ok})
            self._log(ts, "main", "tests pass ✓" if ok else "tests fail ✗", "lead", "green" if ok else "red")
        elif failed:
            first = next((l for l in text.splitlines()[1:] if l.strip()), text.splitlines()[0] if text else "")
            self._log(ts, "main", f"bash failed · {first.strip()[:40]}", "lead", "red")
        if failed and "interrupted by user" not in text:  # the hook skips is_interrupt failures too
            key = (cmd.split(" ")[0] if cmd else "") + "|" + norm(text)
            self.fail_keys[key] = self.fail_keys.get(key, 0) + 1
            if self.fail_keys[key] == 2:
                self.seq += 1
                if self.repeat is None:
                    self.repeat = {"seq": self.seq, "ts": ts, "test": bool(TEST_RE.search(cmd))}
                self._log(ts, "main", "same error ×2 · stop and ask", "lead", "red")

    def _notification(self, body, ts):
        g = {k: (r.search(body).group(1).strip() if r.search(body) else "") for k, r in TAG_RE.items()}
        if g["tool-use-id"] in self.agents:
            self._finish_agent(g["tool-use-id"], ts, g["status"] or "completed", g["result"])


def load_state(path: str | None, entries: list | None = None) -> State | None:
    st = State()
    if entries is not None:
        for e in entries:
            st.feed(e)
        return st
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                st.feed(json.loads(line))
            except Exception:
                continue  # partial or foreign line
    return st

# ---------------------------------------------------------------- derived view

def derive(st: State, project: str) -> dict:
    cfg_main, cfg_adv = settings_models(project)
    amodels = agent_models(project)
    verifs = [a for a in st.agents.values() if a["type"] == "verifier"]
    first_edit = st.edits[0]["seq"] if st.edits else None
    last_edit = st.edits[-1]["seq"] if st.edits else None

    cp1 = [v for v in verifs if first_edit is None or v["start_seq"] < first_edit]
    cp3 = [v for v in verifs if last_edit is not None and v["start_seq"] > last_edit]
    consulted = st.repeat is not None and (
        any(a["seq"] > st.repeat["seq"] for a in st.advisor) or any(v["start_seq"] > st.repeat["seq"] for v in verifs))
    wakes = (1 if cp1 else 0) + (1 if st.repeat else 0) + (1 if cp3 else 0)
    caught = sum(1 for v in verifs if v["verdict"] == "REFUTED")

    done_verdicts = sorted((v for v in verifs if v["verdict"]), key=lambda v: v["end_seq"])
    latest = done_verdicts[-1] if done_verdicts else None
    reviewing_now = any(v["status"] == "running" and last_edit is not None and v["start_seq"] > last_edit for v in verifs)
    if not st.edits:
        ship, why = False, "no changes"
    elif reviewing_now:
        ship, why = False, "reviewing"
    elif latest is None or latest["start_seq"] < last_edit:
        ship, why = False, "edit after review" if latest else "needs review"
    elif latest["verdict"] != "CONFIRMED":
        ship, why = False, latest["verdict"].lower()
    elif any(t["seq"] > latest["end_seq"] and not t["ok"] for t in st.tests):
        ship, why = False, "tests red"
    else:
        ship, why = True, "confirmed"

    cards = []
    for sub, label, blurb in CARDS:
        runs = [a for a in st.agents.values() if a["type"] == sub]
        run = max(runs, key=lambda a: a["start_seq"]) if runs else None
        model = pretty_model(run["model"]) if run and run["model"] else (amodels.get(sub) or "haiku")
        state = run["status"] if run else "idle"
        note = ""
        if sub == "tests" and st.tests and (not run or st.tests[-1]["seq"] > run["start_seq"]):
            state, note = ("done" if st.tests[-1]["ok"] else "failed"), "via main"
        cards.append({"label": label, "model": model, "state": state, "blurb": blurb, "note": note,
                      "runs": len(runs)})
    if st.repeat and st.repeat["test"]:
        fixed = bool(st.tests) and st.tests[-1]["ok"] and st.tests[-1]["seq"] > st.repeat["seq"]
        cards[0]["badge"] = ("×2 → fixed ✓", "greenbg") if fixed else ("same error ×2", "redbg")

    verifier_running = any(v["status"] == "running" for v in verifs)
    haiku_running = sum(1 for c in cards if c["state"] == "running")
    opus_model = next((pretty_model(v["model"]) for v in verifs if v["model"]), None) or amodels.get("verifier") or cfg_adv or "opus"
    haiku_model = next((c["model"] for c in cards if " " in c["model"]), cards[0]["model"] if cards else "haiku")
    return {
        "main": pretty_model(st.main_model) or cfg_main or "main",
        "haiku": haiku_model, "opus": opus_model,
        "cp": [
            {"on": bool(cp1), "label": "before plan", "sub": _cp_sub(cp1, "plan approved ✓", "plan refuted ✗")},
            {"on": bool(st.repeat), "label": "same error ×2",
             "sub": ("consulted ✓", "green") if consulted else (("not consulted yet", "red") if st.repeat else ("", None))},
            {"on": bool(cp3), "label": "before done", "sub": _cp_sub(cp3, "confirmed ✓", "refuted ✗")},
        ],
        "wakes": wakes, "caught": caught, "advisor": len(st.advisor), "verifier": len(verifs),
        "opus_state": "reviewing" if verifier_running else ("on call" if st.advisor or verifs else "sleeping"),
        "latest": latest, "verifier_running": verifier_running, "next_wake": next((i + 1 for i, c in enumerate([cp1, st.repeat, cp3]) if not c), None),
        "ship": ship, "why": why, "cards": cards, "haiku_running": haiku_running,
        "cards_done": sum(1 for c in cards if c["state"] == "done"),
        "tests_pass": sum(1 for t in st.tests if t["ok"]), "tests_fail": sum(1 for t in st.tests if not t["ok"]),
        "last_test": st.tests[-1] if st.tests else None,
        "edits": len(st.edits), "bash": st.bash, "turns": st.turns, "doing": st.now_doing,
        "cost": st.cost, "log": st.log[-7:], "gates": len(st.gates), "alias": cfg_main or "sonnet",
        "repeat_main": bool(st.repeat and not st.repeat["test"]),
        "model_cost": {pretty_model(k): c for k, c in st.model_cost.items()},
    }


def _cp_sub(runs, ok_text, bad_text):
    if not runs:
        return ("", None)
    v = max(runs, key=lambda r: r["start_seq"])
    if v["status"] == "running":
        return ("reviewing…", "purple")
    return {"CONFIRMED": (ok_text, "green"), "REFUTED": (bad_text, "red")}.get(v["verdict"], ((v["verdict"] or "no verdict").lower(), "yellow"))

# ---------------------------------------------------------------- cell model

PALETTE = {
    "bg": (13, 16, 23), "text": (201, 209, 217), "dim": (110, 118, 129), "faint": (60, 66, 78),
    "orange": (240, 136, 62), "blue": (88, 166, 255), "purple": (171, 140, 255),
    "green": (63, 185, 80), "red": (248, 81, 73), "yellow": (210, 168, 70), "white": (240, 246, 252),
    "redbg": (122, 32, 32), "greenbg": (24, 80, 40),
}
LANE = {"lead": "orange", "swarm": "blue", "review": "purple", "gate": "yellow"}


class Line:
    __slots__ = ("segs", "n")

    def __init__(self):
        self.segs, self.n = [], 0

    def t(self, s, fg=None, bold=False, bg=None):
        if s:
            self.segs.append((s, fg, bold, bg))
            self.n += len(s)
        return self

    def pad(self, w, bg=None):
        if self.n < w:
            self.t(" " * (w - self.n), bg=bg)
        return self

    def fit(self, w):
        """Pad or cut to exactly w columns."""
        if self.n <= w:
            return self.pad(w)
        out, n = Line(), 0
        for s, fg, b, bg in self.segs:
            if n + len(s) > w:
                out.t(s[: w - n - 1] + "…", fg, b, bg)
                break
            out.t(s, fg, b, bg)
            n += len(s)
        return out.pad(w)


def L(*parts) -> Line:
    """L("text", ("text", "green"), ("text", "red", True)) -> Line"""
    ln = Line()
    for p in parts:
        if isinstance(p, str):
            ln.t(p)
        else:
            ln.t(*p)
    return ln


def box(rows, width, color, title=None, title_color=None, style="single", center_title=False):
    tl, tr, bl, br, h, v = {"single": "┌┐└┘─│", "dashed": "┌┐└┘╌╎", "double": "╔╗╚╝═║"}[style]
    inner = width - 2
    top = Line().t(tl, color)
    if title:
        label = f" {title} "
        if center_title:
            left = (inner - len(label)) // 2
            top.t(h * left, color).t(label, title_color or color, True).t(h * (inner - left - len(label)), color)
        else:
            top.t(h, color).t(label, title_color or color, True).t(h * (inner - 1 - len(label)), color)
    else:
        top.t(h * inner, color)
    top.t(tr, color)
    out = [top]
    for r in rows:
        ln = Line().t(v, color).t(" ")
        for s in r.fit(inner - 2).segs:
            ln.t(*s)
        out.append(ln.t(" ").t(v, color))
    out.append(Line().t(bl, color).t(h * inner, color).t(br, color))
    return out


def hcat(blocks, gaps):
    """Place blocks (lists of Lines with equal width) side by side, top-aligned."""
    height = max(len(b) for b in blocks)
    widths = [max((l.n for l in b), default=0) for b in blocks]
    out = []
    for i in range(height):
        ln = Line()
        for j, b in enumerate(blocks):
            row = b[i] if i < len(b) else Line()
            for s in row.fit(widths[j]).segs:
                ln.t(*s)
            if j < len(gaps):
                ln.t(" " * gaps[j])
        out.append(ln)
    return out


def bar(state, width, tick):
    if state == "done":
        return ("█" * width, "green")
    if state == "failed":
        return ("█" * width, "red")
    if state == "running":
        pos = tick % (width + 4) - 4
        cells = "".join("▓" if pos <= i < pos + 4 else "░" for i in range(width))
        return (cells, "blue")
    return ("░" * width, "faint")

# ---------------------------------------------------------------- frame

def clock(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else "--:--:--"


def frame(view: dict | None, meta: dict, tick: int = 0) -> list[Line]:
    lines: list[Line] = []
    live = meta.get("live")
    dot = ("● DEMO", "yellow") if meta.get("demo") else (("● live", "green") if live else ("○ idle", "dim"))
    lines.append(L(("CLAUDE CODE", "white", True), ("  ·  ", "dim"), ("3 MODELS", "white", True), ("  ·  ", "dim"),
                   ("OPUS REVIEWS", "white", True)).pad(W - len(dot[0]) - 1).t(dot[0], dot[1], True).t(" "))
    if view is None:
        lines.append(L(("─" * W, "faint")))
        msg = meta.get("waiting", "waiting for a Claude Code session in this project…")
        for _ in range(3):
            lines.append(Line())
        lines.append(L("  ", (msg, "dim")))
        lines.append(L("  ", ("start `claude` here; this window follows the newest session automatically", "faint")))
        for _ in range(3):
            lines.append(Line())
        return [l.fit(W) for l in lines]

    v = view
    lines.append(L(("■ ", "orange"), (f"{v['main']} · lead", "dim"), ("     ■ ", "blue"), (f"{v['haiku']} · swarm", "dim"),
                   ("     ■ ", "purple"), (f"{v['opus']} · reviewer", "dim")))
    lines.append(L(("─" * W, "faint")))

    # ---- left: Opus card
    left_rows = [L(("reviewer · ", "dim"), (v["opus_state"], "purple" if v["opus_state"] != "sleeping" else "dim"))]
    blurbs = [["fresh context", "reads plan +", "diff only"],
              ["never writes", "code"],
              ["last question:", "did i miss", "anything?"]]
    for i, cp in enumerate(v["cp"]):
        mark, col = ("◆", "purple") if cp["on"] else ("◇", "faint")
        left_rows.append(L((mark + " ", col), (cp["label"], "white" if cp["on"] else "dim", cp["on"])))
        sub, scol = cp["sub"]
        left_rows.append(L("  ", (sub, scol)) if sub else Line())
        for b in blurbs[i]:
            left_rows.append(L("  ", (b, "faint")))
    left_rows.append(L(("─" * 26, "faint")))
    left_rows.append(L(("WAKES", "dim", True), "          ", ("CAUGHT", "dim", True)))
    caught = str(v["caught"]) if v["caught"] else "—"
    left_rows.append(L((f"{v['wakes']}/3", "purple", True), " " * (15 - len(f"{v['wakes']}/3")),
                       (caught, "red" if v["caught"] else "dim", True)))
    left_rows.append(L((f"advisor {v['advisor']} · verifier {v['verifier']}", "dim")))
    left = box(left_rows, LEFT, "purple", f"OPUS {v['opus'].split(' ', 1)[-1]}".upper() if " " in v["opus"] else "OPUS",
               "purple", center_title=True)

    # ---- right column
    r: list[Line] = []
    main_rows = [
        L(("writes code + runs tests", "text")).pad(34).t(f"edits {v['edits']} · bash {v['bash']} · turns {v['turns']}", "dim"),
        L((f"--model {v['alias']}", "dim")).pad(34).t("now ", "dim").t(v["doing"] or "idle", "orange"),
    ]
    r += box(main_rows, RIGHT, "orange", f"{v['main'].upper()} · main session", "orange", center_title=True)
    r.append(L(" " * 17, ("delegate to subagents · ", "dim"), (v["haiku"], "blue", True)).fit(RIGHT))
    cards = []
    for c in v["cards"]:
        col = {"failed": "red", "done": "blue", "running": "blue"}.get(c["state"], "faint")
        b, bcol = bar(c["state"], 11, tick)
        status = {"done": ("done ✓", "green"), "failed": ("fail", "red"), "running": ("running", "blue"),
                  "idle": ("idle", "dim")}[c["state"]]
        rows = [L((c["model"], "dim")),
                L((b, bcol), " ", status),
                L((c["blurb"], "text")),
                L((c["badge"][0], "white", True, c["badge"][1])) if c.get("badge") else
                L((c["note"] or (f"runs {c['runs']}" if c["runs"] else ""), "dim"))]
        cards.append(box(rows, 22, col, c["label"], "red" if c["state"] == "failed" else "blue"))
    r += hcat(cards, [1, 1])
    r.append(L(" ", ("1 check = 1 property", "dim")).fit(RIGHT))
    lt = v["last_test"]
    lead_rows = [L(("re-runs tests · plan + diff", "text")),
                 L((f"tests {v['tests_pass']} pass · {v['tests_fail']} fail", "dim"),
                   (f"   last {'✓' if lt['ok'] else '✗'} {clock(lt['ts'])}", "green" if lt["ok"] else "red") if lt else ("", None))]
    if v["repeat_main"]:
        lead_rows.append(L(("same error ×2", "white", True, "redbg"), ("  stop editing · ask opus", "dim")))
    mc = v["model_cost"]
    if mc:
        row = L(("cost ", "dim"))
        for name, col in ((v["main"], "orange"), (v["haiku"], "blue"), (v["opus"], "purple")):
            if name in mc:
                row.t(f"{name.split(' ')[0]} ", col).t(f"${mc[name]:.2f}   ", "text")
        lead_rows.append(row)
    r += box(lead_rows, RIGHT, "orange", f"back to {v['main']} · lead", "orange", center_title=True)
    lt_verdict = v["latest"]
    if v["verifier_running"]:
        rv = [L(("> ", "purple"), ("reviewing diff", "white"), (" " + bar("running", 12, tick)[0], "purple"))]
    elif lt_verdict:
        col = {"CONFIRMED": "green", "REFUTED": "red"}.get(lt_verdict["verdict"], "yellow")
        rv = [L(("> VERDICT: ", "purple"), (lt_verdict["verdict"], col, True))]
    else:
        rv = [L(("> waits for wake ", "dim"), (str(v["next_wake"] or 3), "purple", True))]
    rv.append(L(("FRESH CONTEXT", "purple", True), (" · plan + diff only", "dim")))
    review = box(rv, 55, "purple", f"{v['opus'].upper()} · REVIEW", "purple", style="dashed")
    sc = "green" if v["ship"] else "faint"
    short = {"confirmed": "ready ✓", "needs review": "review", "edit after review": "stale", "tests red": "red ✗",
             "no changes": "empty", "refuted": "refuted", "inconclusive": "unsure", "reviewing": "review…"}.get(v["why"], v["why"][:7])
    ship = box([L(("SHIP", sc if v["ship"] else "dim", True)), L((short, "green" if v["ship"] else ("red" if v["why"] in ("tests red", "refuted") else "dim")))], 11, sc)
    r += hcat([review, ship], [2])

    lines += hcat([left, r], [GAP])

    # ---- session log
    log_rows = []
    for ev in v["log"]:
        who_col = LANE.get(ev["lane"], "dim")
        who = {"main": v["main"], "advisor": v["opus"], "gate": "stop gate", "verifier": v["opus"]}.get(ev["who"], ev["who"])
        if ev["lane"] == "swarm" and ev["who"] not in ("main",):
            who = pretty_model(ev["who"]) if ev["who"].startswith("claude-") else v["haiku"]
        log_rows.append(L((clock(ev["ts"]), "dim"), "  ", (f"{who:<12}", who_col, True), " ",
                          (f"{ev['what'][:58]:<60}", ev["color"] or "text"), " ",
                          ({"lead": "lead", "swarm": "swarm", "review": "review", "gate": "gate"}[ev["lane"]], "faint")))
    while len(log_rows) < 7:
        log_rows.insert(0, Line())
    lines += box(log_rows, W, "faint", "SESSION LOG", "dim")

    # ---- prompt + status line
    cursor = "█" if tick % 2 == 0 else " "
    lines.append(L(("~/" + meta.get("project_name", "app") + " $ ", "dim"), (f"claude --model {v['alias']}", "white"), (cursor, "white")))
    haiku_state = "swarming" if v["haiku_running"] else ("done" if v["cards_done"] else "idle")
    cost = f"${v['cost']:.2f}" if isinstance(v["cost"], (int, float)) else "$—"
    lines.append(L(("haiku ", "blue"), (f"[{haiku_state}]", "blue", True), ("   subagents ", "dim"),
                   (f"[{v['cards_done']}/3]", "white", True), ("   opus ", "purple"), (f"[{v['opus_state']}]", "purple", True),
                   ("   caught ", "dim"), (f"[{v['caught'] or '-'}]", "red" if v["caught"] else "white", True),
                   ("   cost ", "dim"), (cost, "white", True)))
    return [l.fit(W) for l in lines]

# ---------------------------------------------------------------- backends

def to_ansi(lines, color=True) -> str:
    if not color:
        return "\n".join("".join(s for s, *_ in l.segs) for l in lines)
    out = []
    for l in lines:
        buf = []
        for s, fg, bold, bg in l.segs:
            codes = []
            if bold:
                codes.append("1")
            if fg:
                codes.append("38;2;%d;%d;%d" % PALETTE[fg])
            if bg:
                codes.append("48;2;%d;%d;%d" % PALETTE[bg])
            buf.append(f"\033[{';'.join(codes)}m{s}\033[0m" if codes else s)
        out.append("".join(buf))
    return "\n".join(out)


def to_html(lines, title) -> str:
    css_color = lambda k: "rgb(%d,%d,%d)" % PALETTE[k]
    rows = []
    for l in lines:
        parts = []
        for s, fg, bold, bg in l.segs:
            st = []
            if fg:
                st.append(f"color:{css_color(fg)}")
            if bg:
                st.append(f"background:{css_color(bg)}")
            if bold:
                st.append("font-weight:700")
            parts.append(f'<span style="{";".join(st)}">{html.escape(s)}</span>' if st else html.escape(s))
        rows.append("".join(parts))
    body = "\n".join(rows)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>
body{{margin:0;background:#05070b;display:flex;justify-content:center;padding:28px}}
.win{{background:{css_color('bg')};border:1px solid #2a303c;border-radius:14px;box-shadow:0 20px 60px #000c;overflow:hidden}}
.bar{{display:flex;align-items:center;gap:8px;padding:10px 14px;background:#161b24;border-bottom:1px solid #222a36}}
.d{{width:12px;height:12px;border-radius:50%;background:#3b4250}}
.t{{flex:1;text-align:center;color:#8b949e;font:13px 'JetBrains Mono','DejaVu Sans Mono',monospace;margin-right:52px}}
pre{{margin:0;padding:16px 18px 18px;color:{css_color('text')};font:14px/1.42 'JetBrains Mono','DejaVu Sans Mono',monospace}}
</style></head><body><div class="win"><div class="bar"><span class="d"></span><span class="d"></span><span class="d"></span>
<span class="t">{html.escape(title)}</span></div><pre>{body}</pre></div></body></html>"""

# ---------------------------------------------------------------- session discovery

def find_transcript(project: str, session: str | None) -> str | None:
    state = os.path.join(project, ".claude", "state")
    pointers = []
    for f in glob.glob(os.path.join(state, "session-*.json")):
        try:
            d = json.load(open(f))
            if session and d.get("session_id") != session:
                continue
            pointers.append((os.path.getmtime(f), d.get("transcript_path")))
        except Exception:
            pass
    for _, p in sorted(pointers, reverse=True):
        if p and os.path.exists(p):
            return p
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    slug = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(project))
    pattern = os.path.join(base, "projects", slug, (session or "*") + ".jsonl")
    found = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return found[0] if found else None

# ---------------------------------------------------------------- demo session
# A scripted, clearly labelled sample built from the same entry shapes the
# parser reads, so --demo also exercises the real parsing path.

def demo_entries(t0: float = None) -> list[dict]:
    t0 = t0 or datetime(2026, 11, 8, 14, 7, 0).timestamp()
    iso = lambda s: datetime.fromtimestamp(t0 + s, timezone.utc).isoformat().replace("+00:00", "Z")
    E = []
    def a(s, *blocks, model="claude-sonnet-5-5"):
        E.append({"type": "assistant", "timestamp": iso(s), "message": {"model": model, "content": list(blocks)}})
    def u(s, content, **kw):
        E.append({"type": "user", "timestamp": iso(s), "message": {"content": content}, **kw})
    def use(i, name, **inp):
        return {"type": "tool_use", "id": i, "name": name, "input": inp}
    def res(i, text, err=False):
        return {"type": "tool_result", "tool_use_id": i, "content": text, "is_error": err}
    def note(s, i, result):
        u(s, f"<task-notification>\n<tool-use-id>{i}</tool-use-id>\n<status>completed</status>\n<result>{result}</result>\n</task-notification>")

    u(0, "fix the flaky session refresh in src/db")
    a(2, use("x1", "Agent", subagent_type="Explore", description="map src/db"),
         use("x2", "Agent", subagent_type="callsites", description="refreshSession call sites"))
    u(2, [res("x1", "launched")], toolUseResult={"status": "async_launched", "resolvedModel": "claude-haiku-5-5"})
    u(2, [res("x2", "launched")], toolUseResult={"status": "async_launched", "resolvedModel": "claude-haiku-5-5"})
    note(9, "x1", "src/db/session.ts:41 refreshSession ...")
    note(11, "x2", "7 references in 4 files")
    a(14, use("v1", "Agent", subagent_type="verifier", description="review plan"), model="claude-sonnet-5-5")
    u(14, [res("v1", "VERDICT: CONFIRMED\nFINDINGS: none at P0-P2")], toolUseResult={"resolvedModel": "claude-opus-5-5"})
    a(20, use("e1", "Edit", file_path="src/db/session.ts"))
    u(20, [res("e1", "ok")])
    a(24, use("t1", "Agent", subagent_type="tests", description="npm test"))
    u(24, [res("t1", "launched")], toolUseResult={"status": "async_launched", "resolvedModel": "claude-haiku-5-5"})
    note(30, "t1", "npm test: 1 failed")
    a(31, use("b1", "Bash", command="npm test -- session"))
    u(31, [res("b1", "Exit code 1\nFAIL src/db/session.test.ts:88 expected 200 got 401 (412ms)", True)])
    a(36, use("b2", "Bash", command="npm test -- session"))
    u(36, [res("b2", "Exit code 1\nFAIL src/db/session.test.ts:91 expected 200 got 401 (388ms)", True)])
    a(40, {"type": "server_tool_use", "id": "s1", "name": "advisor", "input": {}})
    a(46, use("e2", "Edit", file_path="src/db/session.ts"))
    u(46, [res("e2", "ok")])
    a(50, use("b3", "Bash", command="npm test"))
    u(50, [res("b3", "Tests: 48 passed, 48 total")])
    a(53, use("v2", "Agent", subagent_type="verifier", description="review diff"))
    u(53, [res("v2", "VERDICT: CONFIRMED\nNOT PROVEN BY TESTS: token expiry across DST")], toolUseResult={"resolvedModel": "claude-opus-5-5"})
    a(56, {"type": "text", "text": "Fixed the refresh race; verifier CONFIRMED."})
    E.append({"type": "cost-state", "totalCostUSD": 0.41, "modelUsage": {  # sample figures (DEMO)
        "claude-sonnet-5-5": {"costUSD": 0.14}, "claude-haiku-5-5": {"costUSD": 0.01}, "claude-opus-5-5": {"costUSD": 0.26}}})
    return E

# ---------------------------------------------------------------- main

def render(args, tick=0, demo_upto=None):
    demo_upto = demo_upto or getattr(args, "demo_step", None)
    project = os.path.abspath(args.project)
    meta = {"project_name": os.path.basename(project) or "app", "demo": args.demo}
    if args.demo:
        entries = demo_entries()
        st = load_state(None, entries[:demo_upto] if demo_upto else entries)
        meta["live"] = True
        return frame(derive(st, project), meta, tick)
    path = args.transcript or find_transcript(project, args.session)
    st = load_state(path)
    if st is None:
        return frame(None, meta, tick)
    meta["live"] = time.time() - os.path.getmtime(path) < 60
    return frame(derive(st, project), meta, tick)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--project", default=os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    ap.add_argument("--session", help="session id to follow (default: newest)")
    ap.add_argument("--transcript", help="explicit transcript .jsonl path")
    ap.add_argument("--demo", action="store_true", help="play a scripted sample session (labelled DEMO)")
    ap.add_argument("--once", action="store_true", help="print one frame and exit")
    ap.add_argument("--html", metavar="FILE", help="write one frame as an HTML page and exit")
    ap.add_argument("--demo-step", type=int, help="with --demo: show only the first N sample entries")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args(argv)

    if args.html:
        lines = render(args, tick=7)  # a mid-animation tick, so running bars are visible in a still
        title = "~/" + os.path.basename(os.path.abspath(args.project)) + " · team monitor"
        open(args.html, "w", encoding="utf-8").write(to_html(lines, title))
        return 0
    if args.once or not sys.stdout.isatty():
        print(to_ansi(render(args), color=not args.no_color and sys.stdout.isatty() if not args.once else not args.no_color))
        return 0

    sys.stdout.write("\033[?1049h\033[?25l")
    tick, cache, step = 0, None, 0
    try:
        while True:
            if args.demo:
                n = len(demo_entries())
                step = step + 1 if step < n + 6 else 1   # replay, hold the end for a few seconds
                lines = render(args, tick, demo_upto=min(step, n))
            else:
                lines = render(args, tick)
            cols = shutil.get_terminal_size((W, 40)).columns
            head = "" if cols >= W else f"\033[33mwiden this window to {W} columns (now {cols})\033[0m\n"
            out = head + to_ansi(lines, color=not args.no_color)
            if out != cache:
                sys.stdout.write("\033[H" + out + "\033[J")
                sys.stdout.flush()
                cache = out
            tick += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\033[?25h\033[?1049l")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
