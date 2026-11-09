# Claude Code adapter — feasibility (A4)

**Date:** 2026-11-09. **Status:** feasibility only. No code built, no hooks installed.
**Verified sources (fetched 2026-11-09):** `https://code.claude.com/docs/en/hooks.md` (hooks reference); `https://code.claude.com/docs/en/hooks-guide.md`; `https://code.claude.com/docs/en/plugins/mods/events.md` (JS-function mods, separate surface).

## Hook surface (official docs, verified)

Claude Code hooks are shell commands / HTTP endpoints / LLM prompts / subagents (and, for mods, JS functions). Events fall into per-session (`SessionStart`, `SessionEnd`), per-turn (`UserPromptSubmit`, `Stop`, `StopFailure`), and per-tool (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`) cadences. Inputs arrive as JSON on stdin (command hooks).

| Claude hook | observable (verified) | xCABI mapping |
|---|---|---|
| `SessionStart` | session starts/resumes | `session.open` (agentId=model?) |
| `SessionEnd` | session terminates | flush (no v0 verb; tracer `finish()`) |
| `UserPromptSubmit` | prompt before model processes it | turn boundary (turn counter) |
| `PreToolUse` | `tool_name`, `tool_input`, `tool_use_id`; can block/modify | `tool_recall` candidate: pending re-call mark consumed by next `page()` (cf. `packages/node/src/tracer.ts` `recall`) |
| `PostToolUse` | `tool_input` + `tool_response` (tool-specific schema); paths absolute | `page.declare` (`logicalRef=tool:<name>(canonicalArgs)`, `contentHash=sha256(tool_response)`, `tokens=approx4`) |
| `PostToolUseFailure` | tool failed | **no page** (T6 error rule) |
| `PostToolBatch` | batch of parallel calls resolved | no single xCABI verb; observe as turn boundary |
| `Stop` / `StopFailure` | turn ends (success / API error) | **NO `turn.render`** — Claude does not expose the rendered request, so residency totals are unknowable |
| `PreCompact` / `PostCompact` | context compaction before/after | `page.declare` kind=`summary` for the compaction output (cf. `design/adapters.md` OpenCode risk 4); mapping of removed pages deferred |
| `MessageDisplay` | assistant text while it streams (display-only) | `identifier_scan` candidate — text deltas; but it is a display event, not a model-output contract; mark as experimental |
| `SubagentStart/Stop`, `TaskCreated/Completed`, `PermissionRequest/Denied`, `Notification`, `Elicitation*` | — | no xCABI equivalent (no subagent/permission/fault source); ignore |

## What is NOT observable (stated plainly)

1. **The rendered request is not visible.** No hook carries `messages[]` or `residentTokens`. A Claude Code trace therefore **cannot emit `turn.render`** — it must be labelled as such (same honesty rule as `-z` captures: a trace without `turn.render` says so).
2. **Token counts are unknowable** (no provider usage, no BPE budget in hook input). Declared `tokens` stays `approx4-char` estimated.
3. **System prompt / tool schemas / compaction contents** are not in hook input (only `tool_input`/`tool_response`).

## Prototype (local, zero spend — not built)

A `PreToolUse` + `PostToolUse` shell-hook pair (`jq`-parsed stdin, appends one JSONL line per call) would produce a parseable predecessor trace. It is three hook entries in `.claude/settings.json` or a plugin `hooks.json`. Not implemented in this card; the mapping above is the feasibility output.

## Gaps

- `turn.render`/`call.meta.residentTokens` cannot be produced → metrics (`net_token_reduction`, `touch_ratio`) underivable.
- `identifier_scan` depends on `MessageDisplay`, whose docs call it display-only.
- Tool *output shape varies by tool* (docs: "The exact schema for both depends on the tool") — `approx4` needs per-tool serialisation, not a single rule.
- No subagent identity: `SubagentStart` exists, but xCABI has no subagent page kind.

## Verdict

Feasible as a **mirror-only `page.declare` + `page.fault` tracer** (declare/fault lifecycle) with a permanent **no-`turn.render`** label. Not feasible as a residency/accounting adapter. Effort: ~1 evening for the hook pair; honesty cost: the trace cannot support cost claims.
