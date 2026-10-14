---
name: html-output
description: Use when Joshua asks for a report, spec, plan, code review, status update, comparison, diagram, dashboard, or any deliverable he'll read/share/interact with — deliver it as a self-contained HTML file instead of long Markdown. Covers when to use HTML vs plain text, the self-contained file rules, and the interactive "export back to text" pattern.
---

# HTML as an Output Format

Prefer a **self-contained HTML file** over long Markdown for deliverables Joshua will read, share, or interact with. Based on Anthropic's [The Unreasonable Effectiveness of HTML](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html) and the [html-effectiveness gallery](https://github.com/anthropics/html-effectiveness) (20 standalone examples).

**Mental model:** `CLAUDE.md` is the INPUT (how I work — Joshua's rules/standards/operating model, read every session). HTML is the OUTPUT (how I deliver the result — a browser-openable artifact). They stack; HTML never replaces CLAUDE.md.

## Outcome & SOP Fit

Serves O4 (Productivity/Quality/Learning) primarily; O2 (Dashboard product — shareable, professional reports/specs) and O3 (Live Trading Agent — plans, backtest/paper reports with charts) directly benefit.
SOP stage: **VERIFY** (review/plan artifacts) and **SHIP/DOC** (reports, runbooks, writeups). The HTML file persists as a reference across sessions and as context for verification subagents.

---

## When to use HTML

Reach for an HTML file when the deliverable is:
- **Long** — anything past ~100 lines of Markdown (nobody scrolls a wall of text).
- **Visual** — diagrams, tables, charts, color-coded severity, rendered diffs, design tokens.
- **Shared** — a spec/report/PR writeup someone else needs to actually read.
- **Interactive** — anything Joshua will *tweak* (reorder, toggle, tune sliders) rather than just read.

## When NOT to use HTML

Keep it plain text for: quick conversational answers, a few lines of code, throwaway output, or anything Joshua reads once and discards. HTML costs more tokens than Markdown — spend that cost only when the expressiveness or shareability earns it.

---

## Hard rules for the file

1. **One self-contained `.html`.** No build step, no bundler, no framework.
2. **No external dependencies / no CDNs.** Inline all CSS, JS, and SVG so it opens offline in any browser and survives being emailed or uploaded. (Verify: no failed network requests in devtools.)
3. **Responsive** — readable on mobile, not just desktop.
4. **Persist it** — save into the project (e.g. `tasks/<project>/artifacts/*.html` or `docs/`), don't just dump it in chat. It becomes a durable reference for later sessions and for subagents.

## The export pattern (the part that makes it powerful)

Any **interactive** artifact must end with an export control — a "Copy as Markdown / JSON / prompt" button that serializes the user's edits back to text. This turns the artifact into a control surface: Joshua tweaks the UI, exports, and pastes the result into the next prompt or into git. Without this, an interactive file is a dead end.

---

## Pattern catalog

Map the request to a proven template (full gallery: [anthropics/html-effectiveness](https://github.com/anthropics/html-effectiveness)):

| Request | Pattern |
|---|---|
| "make a plan / spec" | Implementation plan — timeline, data-flow diagram, mockups, risk callouts |
| "review this PR" | Annotated diff with margin notes + severity color-coding |
| "explain this PR / change" | PR writeup — motivation, before/after, file-by-file tour |
| "how does X work / map the code" | Module/architecture map — boxes + arrows, entry points highlighted |
| "compare approaches / designs" | Side-by-side grid of N variants with trade-offs inline |
| "status / weekly report" | Shipped/slipped items + charts |
| "post-mortem / incident" | Minute-by-minute timeline + checklist |
| "design system" | Interactive color/type/spacing tokens as copyable swatches |
| "reprioritize / triage" | Draggable cards + **export to Markdown** |
| "tune this prompt / config" | Live editor with variable slots + **export** |

---

## Relationship to CLAUDE.md (say this if Joshua is unsure)

- `CLAUDE.md` / `rules/` = **input** — instructions Claude reads to know *how to work*.
- `html-output` = **output** — the format Claude delivers results in.
- They are different layers and stack cleanly. Adopting HTML output changes nothing about CLAUDE.md.
