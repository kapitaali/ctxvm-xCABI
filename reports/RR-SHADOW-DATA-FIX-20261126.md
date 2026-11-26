# RR-SHADOW-DATA-FIX-20261126 — exact PageId joins and per-session shadow failures

Lane: hermes. Date 2026-11-26. Scope: the two blockers in
`RR-SHADOW-LIVE-DATA-REVIEW-20261126`. Plugin **0.13.36 → 0.13.37**.

## 1. What was done

- `Tracer.refs_for_identity_tokens()` accepts an optional exact `content_hash`.
  With it, a unique historical `ref|contentHash` declaration wins. Identity tokens
  disambiguate only when several refs share that exact hash. No exact match, or
  several unresolved exact matches, still fails closed.
- `_write_shadow_record()` passes the payload's exact `contentHash` into that
  resolver for dropped and repositioned pages.
- Shadow write failures are now counted per session. Coverage keeps
  `shadowWriteFailures` as the session value and adds the explicitly labelled
  process-wide `shadowWriteFailuresProcess`.
- Added four regressions: ambiguous identity tokens, empty engine identity tokens,
  unique exact hash despite nonmatching tokens, and two-session failure isolation.

## 2. Root cause confirmed from live artefacts

The two swallowed writes at 19:56:43 and 19:57:58 were reconstructed from the
`w8-shadow` session store. Both dropped `L2.md`. The engine produced an **empty**
identity-token set because `_SPLIT_RE` splits `L2.md` into `L2` and `md`, both below
the three-character minimum. The old writer therefore resolved zero refs and
discarded the record. The exact `sha256:882c8708` hash was present and uniquely
identified `tool:read_file({"path":"L2.md"})|sha256:882c8708` in tracer history.

The review's "ambiguous identity-token join" description was directionally right
about the missing exact-hash join, but the measured live failure was a zero-match
empty-token case. The fix covers both shapes.

## 3. Verification

Red-before, from the named tests:

```text
test_ambiguous_identity_tokens_use_exact_content_hash
  FAILED: page_id used the first shared-token ref
test_empty_identity_tokens_use_unique_exact_content_hash
  FAILED: selection.jsonl was not written
test_unique_exact_hash_resolves_despite_nonmatching_identity_tokens
  FAILED: selection.jsonl was not written
test_shadow_write_failures_are_isolated_by_session
  FAILED: second session inherited shadowWriteFailures=1
```

Green after the fixes:

```text
python3 -m pytest packages/hermes/test/test_shadow_mode.py -q
17 passed

python3 -m pytest packages/hermes -q
264 passed, 15 subtests passed

bash tools/run-ci.sh
ALL GATES GREEN
rust; tokenizer; release binaries; node build parity 21 events;
ts 30+62+46+35; python 264+8+66; schema 682 checks; export; hub

bash tools/sync-plugin.sh --check
repo/installed/manifest 0.13.37; installed import OK; gateway stale
```

Installed-copy replay of the two real failed session shapes:

```text
local-ab5842b06f8c dropped 1 floor 16272 budget 24000 resident 32287 failures 0 process 0
local-263e8485d8de dropped 1 floor 16243 budget 24000 resident 32240 failures 0 process 0
INSTALLED_SHADOW_FIX_OK 2 records
shadow schema: OK (2 records)
```

Durable private evidence:
`~/.local/state/ctxvm/w8-runs/shadow-fix-20261126/installed-replay-mmm0gggv/`,
`installed-replay-final.log`, `installed-replay-final.sha256`, `ci-baseline.log`, `ci-final.log`.

## 4. Deviations

None from the routed follow-up. The live acceptance run is not claimed: the
running gateway (pid 90481) still holds 0.13.36 and requires an operator restart.

## 5. Discoveries

- Exact content hash is the authoritative join key; identity tokens are a
  disambiguator, not a prerequisite.
- The live zero-match cause was empty engine tokens from dotted basenames, not
  multiple resolved refs.
- A process-wide failure total remains useful diagnostics but must not gate an
  unrelated session.

## 6. Open questions / next acceptance

After the operator restarts the gateway on 0.13.37, run a fresh `w8-shadow`
session with an evictable middle. Require at least one persisted record with
`floor_tokens < budget_tokens < resident_tokens`, nonempty `dropped_pages`, valid
schema/checker/replay, and zero per-session failures. Candidate pins remain
offline-only. No causal, cost-saving, paging-quality, model-quality, determinism,
availability, or redaction claim is made.
