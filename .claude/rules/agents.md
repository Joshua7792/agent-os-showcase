# Agents

## Design philosophy
Each agent embodies the **highest-level senior version of its real-world role** (principal engineer, staff architect, CISO-grade security lead). Before building a new agent, research the real SOP/responsibilities for that senior role; encode them; give least-privilege tools; register it here. Agents are single-purpose and hand off to each other.

`.claude/agents/*.md` are Claude Code subagents. Claude auto-delegates to them by their `description` triggers ("Use PROACTIVELY", "MUST BE USED"). They run inside Claude Code with scoped tools (the `tools:` front-matter list).

## Active roster (TypeScript/Node default stack)
| Agent | Role | SOP stage | Model |
|---|---|---|---|
| planner | Principal planning specialist | PLAN | opus |
| architect | Staff architect, ADRs, scalability | PLAN | opus |
| tdd-guide | TDD enforcer (RED-GREEN-REFACTOR) | BUILD | sonnet |
| build-error-resolver | Minimal-diff TS/build fixer | BUILD/VERIFY | sonnet |
| code-reviewer | Principal code review | VERIFY | sonnet |
| security-reviewer | CISO-grade security / OWASP | VERIFY | opus |
| refactor-cleaner | Dead-code / duplication cleanup | VERIFY/SHIP | sonnet |
| e2e-runner | Senior E2E (Playwright MCP) | VERIFY (UI) | sonnet |
| doc-updater | Docs / codemaps from source | SHIP/DOC | sonnet |

## Reserve (activate per stack)
| Agent | Activate when |
|---|---|
| database-reviewer | Using Postgres/Supabase (e.g. the dashboard product's data layer) |
| go-reviewer / go-build-resolver | Working in Go |

Chain them with `/orchestrate` (e.g. feature = planner → tdd-guide → code-reviewer → security-reviewer). See [operating-model](operating-model.md).
