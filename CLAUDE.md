## Model routing and verification

Main session (Sonnet) owns reasoning, code edits and the final decision.
The Opus advisor (`advisorModel`) sees the whole transcript; the `verifier`
subagent (Opus, fresh context) sees only the plan and the diff. Use both.

### Delegate (Haiku, read-only)
- Repository mapping → `Explore`. Call sites before changing anything
  shared → `callsites`. Long test or lint runs → `tests`.
- Run independent delegations in parallel. Small single-file reads stay in
  the main session. Workers don't read this file: restate any rule they need.
- Scout output is evidence, not truth: re-check any fact a decision rests on.

### Plan gate (non-trivial work only)
Non-trivial = touches more than one module, changes a default, branching
logic, data shape, auth, money or migrations, or is hard to undo.
1. Write `.claude/plan.md`: goal, scope, non-goals, files, definition of
   done stated as checks that can be run.
2. Call `verifier` on the plan. Revise until it has no P0-P2 findings.
3. Show me the plan and wait for my go-ahead before the first edit.

### Repeated failure
When the same error or failing test shows up a second time, stop editing.
Consult the advisor (or the `verifier` with the plan) on root cause
before a third attempt. A hook reminds you; don't wait for it.

### Done gate
Before saying a non-trivial task is done:
1. Run the checks named in the plan (via `tests`).
2. Call `verifier` with the plan path and base ref. REFUTED → fix and
   re-verify. INCONCLUSIVE → say what evidence is missing.
3. Ask yourself "Did I miss anything?" and act on the answers.
4. Report in this order: commands run and their output, decisions and
   assumptions you made for me, what the tests don't prove, then summary.
