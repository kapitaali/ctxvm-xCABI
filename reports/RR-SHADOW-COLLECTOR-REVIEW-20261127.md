# RR-SHADOW-COLLECTOR-REVIEW-20261127 — blocked: collector needs a focused correctness pass before live use

Review lane, verify-then-record. Subject: `1ec95ae`, `tools/collect-shadow.py` and
`tools/test_collect_shadow.py`. Date 2026-11-27. No live session, model call, spend, gateway/profile change,
or push.

## 1. What passed

- Focused suite: **24 passed, 31 subtests**.
- Full `run-ci.sh`: **ALL GATES GREEN**.
- Pristine-tree rehearsal: **4/4 jobs green**.
- `py_compile`, kit, hygiene, diff, CJK, and production secret/home-path scans pass.
- `--preflight-only` passes against the live 0.13.37 gateway with a temporary SHA-256-pinned manifest.
- Fresh private fixture copies, hash checks, pooled dual views, aggregate privacy filtering, and offline-only pin
  markers are present.

These passes do not clear the blockers below.

## 2. Confirmed blockers

### 2.1 The frozen 12-session target is not enforced

`preflight()` accepts any positive multiple of three up to 12 (`tools/collect-shadow.py:731–734`), and the CLI
exposes it. A no-model probe with `--target-informative 3 --preflight-only` exited 0. The owner authorized 12 new
informative sessions, four per shape; 3 or 9 must not be accepted for a live run. Tests may use reduced targets only
through an explicit test-only seam.

### 2.2 Preflight does not prove fallback is disabled

The requested model/provider are pinned, but preflight never checks `fallback_providers`, `fallback_model`, or an
equivalent effective setting (`tools/collect-shadow.py:368–370,764–778`). A configured fallback can return rc=0 from
another route, violating the no-paid-fallback/no-silent-switch ruling. Preflight must prove the effective fallback
chain is empty or explicitly disabled for this run.

### 2.3 Model/provider drift does not stop collection; `unknown` is accepted

`tools/collect-shadow.py:450–469` accepts `observed_provider == "unknown"` and treats known model/provider drift as
an ordinary failed gate. Only `auth_model_failure` stops the run. A wrong or unproven route can therefore be followed
by more attempts. Any observed route drift or unknown route must stop the batch and be recorded.

### 2.4 Auth/model failure detection misses standard signatures

`_auth_model_failure()` (`tools/collect-shadow.py:249–258`) misses signatures including `invalid_api_key`,
`invalid token`, `token expired`, `access denied`, `model_not_found`, `is not a valid model`, `unknown model`,
`unsupported model`, and `is no longer free`. Those failures can be treated as ordinary excluded attempts instead of
stopping collection. Add table-driven regressions for the supported Hermes/provider error shapes.

### 2.5 Malformed evidence can crash after a model call

After schema/checker failures, the collector still assumes nested coverage/record types. For example,
`record.get("policy", {}).get("mode")` (`tools/collect-shadow.py:475`) raises `AttributeError` when `policy` is a
string. Malformed coverage can similarly fail at `:316–326`. The top-level catches only `PreflightError` (`:858–860`),
so this escapes as exit 1 without the promised excluded-attempt receipt/aggregate. Evidence parsing must be
fail-closed per attempt and always produce a receipt.

### 2.6 Profile overrides are not bound to the launched session

Preflight validates `cfg.profile_home` and `cfg.hermes_home`, but the launch command (`:368–372`) relies on ambient
`HERMES_HOME` plus `-p w8-shadow`; sync also runs with the ambient environment (`:755–762`). A custom
`--hermes-home`/`--profile-home` can therefore validate one tree while the session uses another. Propagate the exact
validated root/profile into both sync and session subprocess environments and verify the effective profile.

### 2.7 New-session uniqueness is not enforced explicitly

Quotas count attempt entries and never deduplicate session IDs (`:648–706`). A simple repeated-SID fake probe was
excluded by evidence mismatch, but the collector still lacks the explicit uniqueness proof required by “12 new
sessions.” Track seen session ids and reject duplicates before they can satisfy any quota.

### 2.8 Per-shape dual-denominator reporting is missing

`_view()` and `denominator_views` (`:596–639,708–713`) produce pooled all-valid and informative-only views. The
`shapes` table has only attempts/valid/informative counts. The owner requires per-shape **and** pooled counts under
both denominator views, without silently conditioning pooled rates. Add per-shape selections, opportunities, rates,
and label counts to both views.

### 2.9 Session-id parsing is too narrow

`_session_id()` parses only stdout (`:303–309,387`). Hermes can emit `session_id:` on stderr and the stdout footer is
a presentation detail. Parse both streams, require exactly one unique durable id, and test stdout-only, stderr-only,
and conflicting-id cases.

## 3. Required fix acceptance

Hermes/tools should:

1. freeze live target to 12/four per shape; reduced targets only in explicit test mode;
2. prove fallback disabled and stop on any observed model/provider drift or unknown route;
3. expand auth/model failure signatures and stop the whole run;
4. make malformed evidence produce an excluded-attempt receipt, never a raw crash;
5. bind subprocess `HERMES_HOME`/profile to the validated paths;
6. enforce unique new session ids before quota credit;
7. emit per-shape and pooled all-valid/informative-only denominator views;
8. parse session ids from both streams;
9. add no-model regressions for every blocker and rerun full CI/rehearsal.

Nice-to-haves: preserve original sidecar bytes alongside normalized gate copies; add one real offline-gate
integration test with synthetic evidence; persist preflight facts in normal runs; normalize remaining preflight I/O
errors to exit 2.

## 4. Verdict

**NOT ACCEPTED for live collection.** The conditional owner authorization remains blocked until this review's
required fixes land and review accepts them. No rates, pins, causal, cost, paging, model, determinism, availability,
or redaction claim.

## 5. Applied

This card, one four-pipe LOG02 row, a day-file section, a PROJECT-STATE blocker update, and a focused hermes/tools
fix prompt. No collector code was changed by review; no push.
