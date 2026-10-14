# Workflow Orchestration

## 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions). Use `/plan` (→ planner agent) to produce a phased, risk-rated plan, then WAIT for confirmation before writing code.
- If something goes sideways, STOP and re-plan immediately — don't keep pushing.
- Write detailed specs upfront to reduce ambiguity.

## 2. Subagent Strategy (keep main context clean)
- Offload research/exploration/parallel analysis to subagents. One focused job per subagent.
- Pass the OBJECTIVE/purpose, not just the literal query; use iterative-retrieval (max 3 cycles) — see the `iterative-retrieval` skill.
- Use `/orchestrate` for multi-agent chains with a structured HANDOFF doc.
- Throw more compute at hard problems via parallel subagents / workflows. Parallel builders each get their own worktree — see the `worktree-lanes` skill.

## 3. Self-Improvement Loop
- After ANY correction from the owner: capture the pattern with `/learn` (→ a learned skill + a note in memory). `tasks/lessons.md` remains the running log.
- Write rules that prevent the same mistake; iterate until the mistake rate drops.
- Review relevant memories/lessons at session start.

## 4. Demand Elegance (Balanced)
- For non-trivial changes, pause: "is there a more elegant way?" If a fix feels hacky, redo it properly.
- Skip this for simple, obvious fixes — don't over-engineer.

## 5. Autonomous Bug Fixing
- Given a bug / failing test / log: just fix it. Point at the evidence, then resolve. Zero hand-holding. Fix failing CI without being told how.

## Task Management
1. **Plan First** — write the plan to `tasks/todo.md` (or `tasks/<project>/todo.md`) with checkable items.
2. **Verify Plan** — check in before implementation on anything that touches core config or is hard to reverse.
3. **Track Progress** — mark items complete as you go.
4. **Explain Changes** — high-level summary at each step.
5. **Document Results** — add a Review to the todo.
6. **Capture Lessons** — update `tasks/lessons.md` / memory after corrections.

See [verification](verification.md) and [operating-model](operating-model.md).
