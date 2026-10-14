# agent-os-showcase

The operating layer I run Claude Code with: an SOP every project follows (coordinate, plan, build, verify, ship,
learn), a roster of role-scoped subagents, a script that gives each parallel builder its own git worktree and merges
it back safely, a status pane, and a command-center snapshot of every project's todo file.

This is a sanitized public copy of my private operating repo ("Joshua-OS"), in daily use since August 2026 to plan
and build a field app, a reporting platform and paper-trading research labs. Project data, memory, client material
and credentials are not here. What is here is the system.

**Honest provenance.** Most agents and skills I operate come from plugins, mainly
[ECC](https://github.com/affaan-m/ECC) (MIT). I assembled and operate that library (66 agents, 90 skills and 14
commands in the private repo). What I built myself is the operating contract, the rules, the scripts, the mod, the
command center, three skills, and senior-role rewrites of twelve ECC agents. The table at the end says which is which,
file by file.

## The operating model

```
 COORDINATE ──► PLAN ──────────► BUILD ─────────────────► VERIFY ───────────► SHIP / DOC ──► LEARN
 main session   planner,         parallel worktree lanes,  code-reviewer,      refactor-      tasks/lessons.md,
 picks agents,  architect;       one builder agent each    security-reviewer,  cleaner,       rules, skills
 outcome +      spec written     (worktree.sh new),        e2e-runner,         doc-updater
 success metric to tasks/todo.md merged behind a backup    tests + coverage
                then WAIT        ref (worktree.sh merge)   gate, evals
```

- **Every plan names the outcome it serves** (`.claude/rules/operating-model.md`). Four outcomes: income, a dashboard
  product, a live trading agent (paper first, always), and the OS itself.
- **Plan and build are separate sessions** (`AGENTS.md` section 1). A planning session ends with the full spec in
  `tasks/todo.md`; a fresh session builds from it.
- **No "done" without evidence** (`.claude/rules/verification.md`): build, typecheck, lint, tests + coverage, secret
  scan. pass@k for "usually works", pass^k = 100% for money, auth and order paths.
- **One status file per project** (`tasks/<project>/todo.md`): a Resume block at the top, a Roadmap of checkable
  stages, a Review log. Boxes are ticked the moment work is verified. See `tasks/example-project/todo.md`.
- **Every correction becomes a rule** (`tasks/lessons.md`, the `worktree-lanes` skill's "Mistakes this skill already
  prevents").

## The roster

| Agent | Role | SOP stage | Model |
|---|---|---|---|
| planner | Principal planning specialist: phased, risk-rated plans | PLAN | opus |
| architect | Staff architect: ADRs, trade-offs, scalability | PLAN | opus |
| tdd-guide | TDD enforcer (red, green, refactor), 80%+ coverage | BUILD | sonnet |
| build-error-resolver | Minimal-diff build and type fixer | BUILD / VERIFY | sonnet |
| code-reviewer | Principal code review | VERIFY | sonnet |
| security-reviewer | CISO-grade security review: OWASP, secrets, money movement | VERIFY | opus |
| refactor-cleaner | Dead code and duplication cleanup | VERIFY / SHIP | sonnet |
| e2e-runner | End-to-end journeys with Playwright MCP | VERIFY (UI) | sonnet |
| doc-updater | Docs and codemaps generated from source | SHIP / DOC | sonnet |
| database-reviewer | Postgres / Supabase schema and RLS (reserve) | VERIFY | sonnet |
| go-reviewer, go-build-resolver | Go review and build fixes (reserve) | VERIFY / BUILD | sonnet |

Each agent file sets its own model and a least-privilege `tools:` list (planner and architect are read-only), and
carries an "Outcome & SOP fit" section. Chain them with `/orchestrate`, e.g. planner → tdd-guide → code-reviewer →
security-reviewer.

## Parallel lanes

`.claude/scripts/worktree.sh` gives each builder subagent its own short-lived git worktree inside the repo, then
merges it back:

```bash
bash .claude/scripts/worktree.sh new lane-a                    # branch wt/lane-a, full checkout in .worktrees/lane-a
bash .claude/scripts/worktree.sh new lane-b --sparse example   # only the paths in .claude/scripts/sparse/example.txt
bash .claude/scripts/worktree.sh list
bash .claude/scripts/worktree.sh merge lane-a                  # refuses dirty overlaps; snapshots main first
bash .claude/scripts/worktree.sh done lane-a                   # remove worktree, delete the merged branch
```

The merge step exists because of a real incident: a raw `git merge` into a main with uncommitted edits failed and
its retry reset about 29 files. The script now refuses when the lane touches any file main has dirty or untracked,
and snapshots main's uncommitted edits to `refs/backup/premerge-<ts>-<name>` before merging. The full orchestration
procedure (design note, frozen shared files, one owner per file, builder prompts, verify each lane yourself) is the
`worktree-lanes` skill. In the private repo, 27 lane merges went through this path.

## Status at a glance

- **`/todo-status` mod** (`.claude/mods/todo-status/`): a Claude Code pane and status line parsed from
  `tasks/todo.md`: current stage, progress, next step, items waiting on the owner, open worktrees. Read-only, with
  tests. Load it with `claude --plugin-dir .claude/mods/todo-status`.
- **Command center** (`tools/command-center/`): `snapshot.py` reads every project's Resume block and
  `tasks/lessons.md` and writes `snapshot.json` + `inbox.json` (stdlib only); `dashboard.html` is the claude.ai
  artifact that renders them.

## Use it

```bash
git clone https://github.com/Joshua7792/agent-os-showcase.git
cd agent-os-showcase
claude                       # CLAUDE.md imports AGENTS.md; .claude/rules, agents and skills load from here
```

Or copy `.claude/` and `AGENTS.md` into your own repo and edit the outcomes in `.claude/rules/operating-model.md`.
Commands such as `/plan`, `/tdd`, `/verify`, `/orchestrate` and skills such as `coding-standards` come from the ECC
plugin; install it to get them.

Checks (the first three run in CI, `.github/workflows/ci.yml`, with a gitleaks secret scan):

```bash
python scripts/check_paths.py                         # every path referenced in this repo resolves
bash scripts/test-worktree.sh                         # worktree.sh end to end in a throwaway repo (6 checks)
python tools/command-center/snapshot.py --out /tmp/cc # snapshot of the example project
claude plugin test .claude/mods/todo-status           # the mod's tests (7); needs the Claude Code CLI
```

## What is built here and what is assembled

| Path | Origin |
|---|---|
| `AGENTS.md`, `CLAUDE.md`, `.claude/rules/*.md` (9) | Written by Joshua (the operating contract and rules) |
| `.claude/scripts/worktree.sh`, `.claude/scripts/sync-skills.ps1`, `scripts/*` | Written by Joshua |
| `.claude/mods/todo-status/` | Written by Joshua on Claude Code's mod API |
| `tools/command-center/` | Written by Joshua |
| `.claude/skills/worktree-lanes`, `fable-mode`, `html-output` | Written by Joshua (`html-output` follows Anthropic's public "HTML as output" guidance) |
| `.claude/agents/*.md` (12) | Rewritten by Joshua from ECC originals (MIT, see `THIRD_PARTY_NOTICES.md`): senior-role SOPs, outcome tags, tool lists |
| Every other agent, skill and command referenced | Not included. From the ECC plugin and other plugins; install them from their sources |

Excluded on purpose: memory, the knowledge base, project todos and data, client-specific agents and skills, personal
skills, third-party skills, bot configuration, CI for private projects, and every credential.

## License

MIT for my work, see [LICENSE](LICENSE). The twelve agent files are derived from MIT-licensed ECC agents; their
notice is in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
