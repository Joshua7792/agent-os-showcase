# Example project — todo

Template. Every project keeps ONE status file like this: a Resume block at the top (read by a fresh session, the
`/todo-status` mod and `tools/command-center/snapshot.py`), a Roadmap of checkable stages, and a Review log.

## ▶ Resume here (updated 2026-10-13)
- **Where:** main. Stage 1 done; stage 2 in progress.
- **Next:** finish lane B (report renderer), then run the stage gate.
- **Before starting:** run the full test suite on main; it must be green.

## Roadmap

- [x] **Stage 1 — foundation** — gate PASSED
  - [x] shared types and boundary tests committed on main before any lane
- [~] **Stage 2 — parallel lanes** (worktrees, see the `worktree-lanes` skill)
  - [x] Lane A: data loader — merged
  - [~] Lane B: report renderer (in progress: worktree lane-b)
  - [ ] Stage gate: code-reviewer + security-reviewer, awaiting Joshua's approval
- [ ] **Stage 3 — ship** — docs from source, runbook

## Review (one line per finished item, newest last)
- Stage 1: types + boundary tests on main; suite green; coverage recorded in the commit message.
- Lane A: merged with `worktree.sh merge lane-a`; full suite re-run on main.
