# Contributing

This repo is a working snapshot of a personal operating system for Claude Code, published so others can read it,
copy it and adapt it. Issues and pull requests are welcome.

- Keep it a system, not a pile of prompts: a new agent, skill or rule says which SOP stage it serves.
- Scripts change test-first: extend `scripts/test-worktree.sh` before changing `.claude/scripts/worktree.sh`, and the
  mod's `tests/status.test.ts` before changing the mod.
- `python scripts/check_paths.py` and `bash scripts/test-worktree.sh` must pass.
- Never commit credentials, memory, personal data or project data. CI runs gitleaks on every push.
- Third-party content keeps its license and attribution (`THIRD_PARTY_NOTICES.md`).
- Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).
