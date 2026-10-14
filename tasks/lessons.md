# Lessons

The running log of the self-improvement loop (`AGENTS.md` section 3). One entry per correction or incident:
what happened, the rule that prevents it, and where the rule now lives. `tools/command-center/snapshot.py` reads
the `## YYYY-MM-DD — title` headings. These entries are the generic ones from the private log.

## 2026-10-11 — A raw git merge into a dirty main wiped uncommitted work
A merge failed with "unable to write .git/index"; the retry aborted and reset ~29 files with uncommitted edits to
HEAD. Rule: merge lanes only with `.claude/scripts/worktree.sh merge`, which refuses overlaps with dirty files and
snapshots main to `refs/backup/premerge-*` first. If a merge fails, stop; never retry blindly.
Lives in: `.claude/scripts/worktree.sh`, `worktree-lanes` skill section 5.

## 2026-10-11 — One edit of a failed batch was silently not re-applied
Two `Edit` calls in one batch failed ("file not read") and only one was re-applied. Rule: after a failed batch,
grep for every intended edit before relying on it.
Lives in: `worktree-lanes` skill, "Mistakes this skill already prevents".

## 2026-10-12 — Builder subagents could not load skills
Builders dispatched as `tdd-guide` have no Skill tool, so "use skill X" silently did nothing. Rule: when a builder
needs skills, dispatch `general-purpose` and make "invoke Skill X" its first action, reported back.
Lives in: `worktree-lanes` skill, "Mistakes this skill already prevents".

## 2026-10-12 — A script that registers a hidden scheduled task was blocked as malware
Antivirus blocked a new `.ps1` mid-merge because it registered a hidden repeating task. Rule: builders never write
scripts that silently register hidden or persistent tasks; if security software objects, change the design.
Lives in: `worktree-lanes` skill, "Mistakes this skill already prevents".
