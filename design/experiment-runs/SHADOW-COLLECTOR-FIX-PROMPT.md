MASTER PROMPT — hermes/tools lane: fix shadow collector review blockers

Authority: `reports/RR-SHADOW-COLLECTOR-REVIEW-20261127.md`. Implementation remains authorized; live collection
remains blocked. Do not run live sessions or edit profile/gateway/model configuration.

## Required fixes

1. **Target:** live `--target-informative` must be exactly 12 (four per shape). Reduced targets allowed only through
   an explicit test-only seam, never a normal live invocation.
2. **Fallback:** preflight must prove the effective Hermes fallback chain is empty/disabled. No paid fallback or
   silent route switch.
3. **Observed route:** require exact model/provider. `unknown` or any drift stops the entire run with a receipt.
4. **Auth/model failures:** expand signature coverage (invalid API key/token, expired token, access denied,
   model_not_found, invalid/unknown/unsupported/no-longer-free model, plus existing 401/403/404 cases). Any match
   stops the whole run.
5. **Malformed evidence:** all coverage/shadow parsing after a failed gate must be type-safe and produce an
   excluded-attempt receipt; no AttributeError/raw exit 1 after a model call.
6. **Profile binding:** pass the validated `HERMES_HOME` and profile root explicitly to both sync and session
   subprocesses; prove the launched profile is the validated one.
7. **New sessions:** deduplicate durable session ids before quota credit; repeated ids never count toward 12.
8. **Denominators:** emit per-shape and pooled `all_valid` and `informative_only` views with selections,
   opportunities, label counts, and rates.
9. **Session id parsing:** parse both stdout and stderr; require one unique id; test stdout-only, stderr-only, and
   conflicting ids.

## Tests

Add no-model regressions for every item. Keep fake runners/temp dirs; no real Hermes/model calls. Run focused suite,
full `run-ci.sh`, `ci-rehearsal.py`, kit, hygiene, diff, CJK, and secret/home scans. Preserve foreign WIP; private
index; append one four-pipe LOG02 row and day section; no push.

Hand back exact diff + verification receipt. Review acceptance is required before any live attempt.
