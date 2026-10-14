# Verification Before Done

Never mark a task complete without proving it works. **Evidence before assertions, always.**

- Run the gate before claiming done: `/verify` (build → typecheck → lint → tests+coverage → secret scan → git status → PASS/FAIL). Modes: `quick` / `full` / `pre-commit` / `pre-pr`. Backed by the `verification-loop` skill.
- Diff behavior between baseline and your change when relevant.
- Ask: "Would a staff engineer approve this?"
- For non-deterministic / agent behavior, use evals (`/eval`, `eval-harness` skill): **pass@k** for "usually works," **pass^k (=100%)** for critical paths (money movement, auth, trading orders).
- If tests fail, say so with the output. If a step was skipped, say that. State "done" only when verified.
