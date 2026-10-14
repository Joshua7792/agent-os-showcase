# Testing

- TDD by default: failing test first → minimal code → refactor, via `/tdd` (→ tdd-guide). 80%+ coverage; 100% on critical/financial/auth/core logic.
- Fill coverage gaps with `/test-coverage`. E2E user journeys via the `e2e-runner` agent (Playwright MCP) before any UI ships.
- Treat agent/LLM behaviors as evals (pass@k vs pass^k) — `eval-harness` skill.
- Test behavior through the public API, not implementation details. No sleeps in tests; fix flaky tests, don't ignore them.
