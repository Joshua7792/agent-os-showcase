# Performance & Context Economy

The context window is the scarce resource. Manage it deliberately.

## Model selection by task
- **Haiku** — search, doc lookup, cheap mechanical work.
- **Sonnet** — default for ~90% of coding/review/PR work.
- **Opus** — architecture, security, hard debugging, planning.
(Subagents already encode a sensible model per role.)

## Context discipline
- Keep **<10 MCPs enabled** and **<80 tools active** — a 200k window can shrink to ~70k under tool bloat. Audit with `/mcp` and `/plugins`; disable what a given task doesn't need.
- Prefer modular files over megafiles. Keep `CLAUDE.md` and `rules/` lean (they anchor every session).
- Compact at logical phase boundaries (after planning, after debugging — never mid-implementation) — `strategic-compact` skill.
- Replace a heavy MCP with a CLI + `/command` when a CLI exists (saves tool budget).
