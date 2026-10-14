# Coding Style

Full reference: the `coding-standards` skill (auto-activates on TS/JS/React/Node work; from the ECC plugin).

- KISS / DRY / YAGNI. Clear over clever.
- Many small files (200–400 lines; 800 max). Match the surrounding code's idioms, naming, and comment density.
- Immutability (no mutation; spread). Centralized error handling. Zod (or equivalent) input validation at boundaries.
- No `console.log` in committed code. Conventional commits. `main` in one working folder is the real code; parallel work uses short-lived git worktrees inside the repo (`.worktrees/<card>`, `.claude/scripts/worktree.sh`), merged back into `main` and deleted the same session — never a long-lived branch or a second copy of the repo elsewhere. Commit/push only when the owner asks.
- Stay stack/DB-agnostic in shared code; confirm the actual framework/datastore before prescribing one (default stack: TypeScript/Node).
- For deliverables you'll read/share/interact with (reports, specs, plans, reviews, diagrams), prefer a self-contained HTML file over long Markdown — see the `html-output` skill.
