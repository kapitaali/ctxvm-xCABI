# RR-CHANNELS-20261109 — A4: four distribution channels

**Date:** 2026-11-09. **Workstream:** A4. No submission, no publish, no prototype built. All sources verified 2026-11-09 (locators in each card).

| channel | card | verdict |
|---|---|---|
| Claude Code hooks | `design/claude-code-adapter.md` | mirror-only declare/fault tracer; **no `turn.render`** (rendered request invisible). Feasible, honesty cost noted |
| OpenCode ecosystem | `design/opencode-distribution.md` | npm `private` + metadata gaps only; submission = owner PR after D17 |
| OTel D3-c | `design/otel-d3c-verified.md` | repo verified (`semantic-conventions-genai`, main, pushed 2026-11-09); mapping = existing layered projection; residency/faults/evictions have no equivalent |
| Hermes catalog | `design/hermes-catalog-submission.md` | community entry draft prepared (YAML above); blocked only on release SHA (D17) |

**Conflicts:** none. New files only in `design/`, no spec/catalog edits.

**Repro:** fetch the four official URLs (links in cards) and re-check `git ls-remote`, `npm view`, `curl api.github.com/repos/open-telemetry/semantic-conventions-genai`. Gates: `tools/check-handoff.sh` PASS, `tools/run-ci.sh` ALL GATES GREEN exit 0.
