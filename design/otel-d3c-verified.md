# OTel D3-c — verified check + mapping (A4, no build)

**Date:** 2026-11-09. **Status:** verified description; exporter described, not built (per prompt).
**Replaces the UNVERIFIED mark:** GenAI semconv status was `UNVERIFIED (vendor blog only)` in `design/otel-mapping.md` sources (2026-10-29). This card verifies against the repo.

## Verification (reproducible, fetched 2026-11-09)

- Repo: `https://github.com/open-telemetry/semantic-conventions-genai` — public, `main` branch, last push `2026-11-09T03:46:58Z`, 528 stars, 140 forks (`api.github.com/repos/open-telemetry/semantic-conventions-genai`). Human docs in `docs/`, YAML in `model/`, reference tooling in `reference/`.
- Move: `https://opentelemetry.io/docs/specs/semconv/gen-ai/` now says "GenAI semantic conventions have moved to the OpenTelemetry GenAI semantic conventions repository" (verified today). Core registry (`/registry/attributes/gen-ai/`) marks GenAI attributes "Moved".
- Stability: docs state semconv attributes carry **Development** badge (per `design/otel-mapping.md` §1, fetched 2026-10-29). The move itself does not stabilise them; the mapping below therefore stays on `gen_ai.*` standard names + `ctxvm.*` extensions, with converter tables that pin semconv `Development` at export time rather than baking names in.

## Mapping (existing, not rebuilt — `design/otel-mapping.md` §2 + `tools/otel-export.mjs`)

- `session.open` → resource attrs + root span `invoke_agent {agentId}` (INTERNAL)
- `turn.render` → span `chat {model}` (CLIENT), child of agent span
- `call.meta.cacheEstimate` → attributes; `gen_ai.usage.cache_read.input_tokens` **only** when `providerReported`, else `ctxvm.*` (D12 law)
- `page.declare` → span `execute_tool {tool}` (INTERNAL), `gen_ai.tool.name`
- `page.render` / `page.fault` / `page.evict` / `pin`/`unpin` → span events `ctxvm.page.render` / `.fault` / `.evict`
- D3-c promotion (2026-11-08, `RR-D3COTEL-20261108`): exporter is the supported lossy projection; drift guard (`otel-export.test.mjs`, 4 tests) keeps `consumed ∪ dropped ∪ type` in sync with RFC-0.1 schema.

## No equivalent in OTel (name plainly)

Residency / headroom (`turn.render.residentTokens`), fault-source taxonomy (`faultOfResidentPage` invariant), stub text, replay determinism, and corpus KPIs (`touch_ratio`, `net_token_reduction`, `thrash_index`) have **no OTel equivalent**. They survive as `ctxvm.*` attributes/events; a backend reading only `gen_ai.*` sees agent/turn/tool spans only.

## Exporter description (not built in this card)

A pure projection: reads xCABI JSONL, emits OTLP/JSON spans. No network, no state. Dropped fields table (e.g. `providerUsage` declared dropped at leaf per D12, `ts` clock omitted per R4 design) is drift-guarded by `tools/otel-export.test.mjs`. Re-run: `node tools/otel-export.mjs <trace.jsonl>` (see `design/otel-mapping.md` §6).

## Gaps

- semconv `Development` — attribute names may shift; the drift guard fails red and forces a mapping review.
- No residency accounting: OTel consumers cannot reproduce `ctxvm replay`.
- `gen_ai.tool.call.id` is Conditionally Required — adapter must supply `tool_use_id` where available (Claude Code Pre/Post hooks carry it, OpenCode payloads carry `id`).
