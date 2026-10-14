---
name: worktree-lanes
description: The orchestrator's repeatable procedure for building one project phase with parallel builder subagents, each in its own short-lived git worktree inside the repo — design note, frozen shared files on main, disjoint lane ownership, builder prompts, verify each lane yourself, merge safely back into main (dirty-main safety net), clean up the same session, tick the todo. Use whenever Claude splits a build into parallel lanes.
---

# Parallel lanes in worktrees (orchestrator)

Written after two builds ran this procedure by hand. Rules live in repo-root `AGENTS.md` (worktrees inside the
repo, merged + deleted the same session). Script: `.claude/scripts/worktree.sh`.

## 1. Before any lane
1. **Design first.** A read-only `architect` agent writes the note (shape, frozen contracts, lane table with ONE owner
   per file, binding test names, traps). Save it to `tasks/<project>/buildN-design.md` and summarise it in the todo.
2. **Step 0 on main, by you.** Write and commit the shared frozen files (types, paths, record builders, boundary/AST
   guard tests) BEFORE creating worktrees, because worktrees branch from main's last commit. Run the full suite first.
3. If two lanes will need the same helper, write it on main yourself now, commit, then
   `git -C .worktrees/<lane> merge --ff-only main` for lanes already created.

## 2. Create lanes
`bash .claude/scripts/worktree.sh new <name>` (full checkout) or `... new <name> --sparse <profile>` (paths listed in
`.claude/scripts/sparse/<profile>.txt`). Check the worktree is populated (`ls`): an empty checkout means the sparse
list is wrong. Mark each item *(in progress: Lane X, worktree <name>)* in the todo.

## 3. Builder prompt (one per lane, run in background, launched in ONE message)
Must state: the worktree path and "work only there"; the files the lane OWNS (everything else read-only, the frozen
file never edited: STOP and report instead); read-first list (design sections + merged code); the exact contract and
signatures; the binding test names; gates (full suite, coverage %, linter, boundary test); "no network, no real
paid calls, no orders"; "do not edit the todo: the orchestrator ticks it"; **"delete `.coverage`, lockfiles and
`*.egg-info` so `git status` is empty"** (the merge script refuses untracked files); commit message + Co-Authored-By
line; "do not merge, push or delete"; a short report.

## 4. When a lane reports
Never trust the report alone. In its worktree, re-run its tests + coverage + linter, and `git diff --stat main...HEAD`
to confirm it touched only owned files. Note deviations for the todo Review.

## 5. Merge
- Merge ONLY with `bash .claude/scripts/worktree.sh merge <name>`, never a raw `git merge`. The script refuses if the
  branch touches any file main has dirty or untracked, and snapshots main's uncommitted edits to
  `refs/backup/premerge-<ts>-<name>` first.
- **If a merge fails, STOP. Do not retry.** Run `git status`; if uncommitted edits vanished, restore them with
  `git checkout refs/backup/premerge-... -- <path>`. Without a snapshot, recover from editor local history and
  Claude Code's file history (`~/.claude/file-history/`). Use a read-only recovery subagent and restore only after
  comparing against HEAD.
- **Stray files after a failed merge:** "Merge with strategy ort failed" while another session was committing on main
  can leave the branch's NEW files untracked in main (no MERGE_HEAD). Check: compare every path in the premerge
  snapshot against the working tree (paths the snapshot records as deleted must still be absent), and
  `git hash-object` each stray file against `wt/<name>:<path>`. Only when all are byte-identical, delete the stray
  files and run the script's merge again. A Git Bash `fork: Permission denied` (exit 254) is the shell failing before
  git runs: nothing happened, inspect with PowerShell, then retry.
- After each merge, run the FULL suite on main (and in any run copy the project deploys to).

## 6. Close out the same session
`bash .claude/scripts/worktree.sh done <name>` for every merged lane; `git worktree list` must show only main. Tick
each todo box with a one-line result (commit, coverage, key numbers) the moment it is verified.

## Mistakes this skill already prevents
- A raw `git merge` into a dirty main hit "unable to write .git/index"; the retry aborted and reset ~29 files with
  uncommitted edits to HEAD. Fixed with the script's refuse + snapshot step and the "stop, don't retry" rule.
- Two `Edit` calls in one batch failed ("file not read") and only one was re-applied. After a failed batch, re-check
  every edit landed (`grep`) before relying on it.
- Build leftovers (lockfiles, `.coverage`, `egg-info`) block merges; builders delete them before committing.
- A merge failed because antivirus software blocked a new `.ps1` as it was written into main (the script registered
  a hidden, repeating scheduled task, which looks like malware persistence). The merge left the branch's new files
  UNTRACKED in main. Recovery: compare each leftover to the branch blob (`git rev-parse wt/<n>:<path>` vs
  `git hash-object --path=<path> <file>`), delete the identical leftovers, fix the branch, merge again. If a file is
  unreadable with "contains a virus or potentially unwanted software", never work around it; change the design.
  Rule for builders: no scripts that silently register hidden/persistent tasks.
- Background shells: `git worktree add` on a large monorepo can exceed 2 min; run it in the background.
- Builders dispatched as `tdd-guide` could NOT load skills (that agent type has no Skill tool). When a builder must
  use skills, dispatch `general-purpose` (all tools) and make "invoke Skill X" its first action + report which loaded.
  `security-review` also fails inside a sparse worktree (no `origin/HEAD`); run it on main after merge, scoped to the
  project path.
