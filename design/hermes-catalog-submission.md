# Hermes plugin index — submission material (A4, not submitted)

**Date:** 2026-11-09. **Status:** prepared, not submitted (owner gate D17).
**Verified source:** `https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog` (What's in an entry / Trust model / Submitting). The catalog is a YAML file per entry in `NousResearch/hermes-agent/plugin-catalog/`, submitted by PR, human-merged, exact-SHA pinned, `hermes plugins validate` + security scan at admission (dangerous = fail, caution = listed). A plugin author never updates the pin themselves.

## Draft entry (prepared — exact key names per docs table)

```yaml
name: ctxvm-tracer
description: Read-only xCABI flight recorder: deterministic JSONL traces of pages, faults and renders for replay and context accounting.
repo: kapitaali/ctxvm-xCABI
sha: <40-hex commit SHA of the release tag>
subdir: packages/hermes
tier: community
category: tools
maintainer: kapitaali
capabilities:
  hooks:
    - on_session_start
    - pre_tool_call
    - post_tool_call
    - pre_llm_call
    - pre_api_request
    - post_api_request
    - on_session_end
  tools: []
requires_hermes: ">=0.19"
version: "0.10.6"
docs_url: https://github.com/kapitaali/ctxvm-xCABI/blob/main/packages/hermes/HOOKS.md
known_issues: "Capture is default-on in owner-run builds; in a registry release the first-run notice is required (D14)."
```

Field notes from docs:
- `subdir` path regex `[A-Za-z0-9._/-]+`, no `..` — `packages/hermes` fits.
- `tier: community` is the only tier a non-Nous plugin can claim (official/verified are Nous-only).
- `sha` must be the exact 40-hex of the release commit; installs check it out, never a branch tip. The entry is *not* submittable until the release commit is pinned (D17 gate).
- `capabilities` must declare tools/hooks/middleware/env — hooks above come from `packages/hermes/live/plugin.yaml` `provides_hooks`.
- `image`/`screenshots`/`onboarding`/`title` omitted (optional).

## What is missing before submission

1. Release commit SHA (owner-gated tag, D17).
2. Hermes version pin re-checked against `live/plugin.yaml` (`version: 0.10.6`) at tag time.
3. Admission CI must pass (`hermes plugins validate` + security scan). Local copy installs today via `hermes plugins install kapitaali/ctxvm-xCABI` w/ subdir, or copying `packages/hermes/live/` (owner-gated git-URL bypasses review; catalog is the reviewed path).

## Verdict

Feasible today as a community entry once pinned to a release commit. The draft above is the PR payload; it is not filed.
