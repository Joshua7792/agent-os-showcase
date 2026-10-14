# Operating Model — the SOP that ties work to outcomes

This is how we run. The goal is a **deployable system**, not random prompts: SOPs, workflows, accountability, and a clear line from every action to an outcome. The thesis: operationalizing agents, not collecting prompts.

## Outcomes (the "why" behind every task)
- **O1 — Business / Income:** ship things that can generate income.
- **O2 — Dashboard product:** a professional, installable, scalable, deployable dashboard that can be standardized across projects.
- **O3 — Live Trading Agent:** careful, risk-controlled, phased (prototype → backtest/paper → guarded live); learn + build expertise; safety first.
- **O4 — Productivity / Quality / Learning:** the operating system itself, plus craft and growth.

Every plan states which outcome(s) it serves. Every agent/skill/command carries an "Outcome & SOP fit" tag.

## The SOP (idea → outcome)
| Stage | What happens | Primary tools |
|---|---|---|
| **0. COORDINATE** | The main assistant frames the task, picks agents/skills/steps, sets the outcome + success metric | `/orchestrate` |
| **1. PLAN** | Restate requirements, phase the work, rate risk, WAIT for confirmation | `/plan` → planner, architect |
| **2. BUILD** | Test-first implementation, minimal diffs | `/tdd` → tdd-guide; `/build-fix` → build-error-resolver; coding-standards, backend/frontend-patterns skills |
| **3. VERIFY** | Prove it works: review, security, tests, evals | `/verify`, `/code-review` → code-reviewer, security-reviewer; verification-loop, eval-harness |
| **4. SHIP / DOC** | Clean up, document from source, runbook | `/refactor-clean`, `/update-docs`, `/update-codemaps` → refactor-cleaner, doc-updater |
| **5. LEARN** | Capture what worked/failed into reusable skills + memory | `/learn`, `tasks/lessons.md`, memory |

## Accountability
- **Per project:** a `tasks/<project>/todo.md` with checkable phases + a Review section; track status as we go.
- **Gates:** no "done" without `/verify` evidence. No risky O3 step skips its paper-trade gate. No sensitive surface ships without `security-reviewer`.
- **Metrics:** every project defines success metrics up front (e.g. dashboard = installable + deploys to N projects; trading = pass^k on order/risk logic + positive paper-trade PnL before live).
- **Checkpoints:** `/checkpoint` named save-states at milestones.

## Project → SOP mapping (examples)
- **Dashboard product (O2):** PLAN the architecture (installable, scalable) → BUILD with frontend/backend-patterns + tdd → VERIFY with code-reviewer + e2e-runner → SHIP with doc-updater + runbook. `database-reviewer` activates for the data layer.
- **Live Trading Agent (O3):** PLAN a phased roadmap (prototype→backtest→paper→guarded live) → BUILD core logic test-first → VERIFY with security-reviewer + pass^k evals on order/risk logic → never go live without a kill switch + paper-trade evidence.

See [workflow](workflow.md), [verification](verification.md) and [agents](agents.md).
