# Agent OS — Claude

@AGENTS.md

Repo notes for Claude Code:
- Rules: `.claude/rules/*.md`. Agents: `.claude/agents/*.md`. Skills: `.claude/skills/*/SKILL.md`.
- Parallel builds: `.claude/scripts/worktree.sh` + the `worktree-lanes` skill. Worktrees live in `.worktrees/`
  (gitignored) and are merged and deleted in the same session.
- Status: `tasks/todo.md` (OS log) and `tasks/<project>/todo.md`; lessons in `tasks/lessons.md`.
- Before committing: `python scripts/check_paths.py` and `bash scripts/test-worktree.sh` must pass.
