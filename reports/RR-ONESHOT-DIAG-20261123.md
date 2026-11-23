# RR-ONESHOT-DIAG-20261123 — oneshot flush diagnostic: on_session_end FIRES; the gap is capture identity + retention

Lane: hermes. Authority: owner "authorize the oneshot flush diagnostic" (step 1 only of
`RR-PARTC-ARM-RESULT`'s proposed scope). One controlled `hermes chat --oneshot` on free tier
(`w8cn-naive`, `meituan/longcat-2.5:free`), $0 launch cost, **no production change, no version bump,
no restart, no push**. Scratch workspace removed by exact path (law 10).

## 1. My premise was wrong

I recommended this diagnostic on the hypothesis that `--oneshot` sessions don't flush. **That is
false.** The controlled oneshot (session `-c diagflush-215128`, `--create-if-missing`) produced:

```
session_start identity={... meituan/longcat-2.5:free}
pre_llm (context)
write-through events=84 traces=2 (partial)
session_end -> flush all tracers
flush 20261123_214951_d39700.jsonl bytes=1155 session=20261123_214951_d39700
flush local-2d8134....jsonl bytes=699  session=local-2d8134...
flush local-b0efb3....jsonl bytes=795  session=local-b0efb3...
... (all live tracers re-flushed)
retention deleted=2 files (max=200, days=30, bytes=536870912)
```

So `on_session_end` fires on `--oneshot`, `_flush_traces()` runs, and **coverage sidecars are written**
(the two new `local-*` files carry `pluginVersion 0.13.30`). There is no missing flush trigger to fix.
A first attempt without `--create-if-missing` failed at rc=1 with "No session found" and produced no
witness lines — it never created a session, so it is not evidence about flushing.

## 2. Where the arm's evidence actually went

Two mechanisms, both outside the flush path:

1. **Capture identity mismatch.** The host names captures by gateway-generated session IDs
   (`local-<hash>` or `20261123_…`), **not** the `-c` session name the driver uses (`partC-stub-paged-01`
   etc.). I asked for `diagflush-215128`; no file of that name exists. The arm's `verify()` looks for a
   capture path derived from the session name and finds none — the same "NO RECORD" shape seen in
   earlier W8 runs. A capture may exist under a different name.
2. **Retention churn.** The trace dir is pinned at the 200-file cap (`CTXVM_TRACE_RETAIN_MAX=200`);
   the diagnostic's own flush deleted 2 files. Eight stub-arm sessions × 21 oneshot prompts each = 168
   invocations, each flushing all live tracers and pruning. Zero traces remain in the arm's time window
   (21:00–21:15 local). Any captures the arm produced were evicted by the cap.

Confirmed: **no** 0.13.30 coverage sidecar anywhere carries `stubDropped: "recoverable"`; the two fresh
oneshot sidecars carry `"off"` (that profile was a control arm). So neither attestation condition can
be recovered from current disk state.

## 3. What follows — no plugin fix justified

The authorized step-2 branch was "only if a plugin-side flush trigger is broken." It is not. Changing
`live/__init__.py` to add another flush hook would be a hack against a **naming/retention** problem, not
a fix. I made **no** plugin change and do not recommend one.

The honest options for closing the attestation gap (each needs a fresh ruling, none taken):
- **Recover forward:** instrument the *profile* (not the plugin) so a `--oneshot` run writes a durable
  per-session capture to the run dir; run one stub session with trace-dir retention raised via env
  (`CTXVM_TRACE_RETAIN_MAX`), then map the host session ID from the `.live.json` stamp to its capture.
  This is runner/harness work (`experiments/**`), not a plugin change.
- **Accept the gap:** keep the accuracy result (1/8 → 7/8) and record stub attestation + re-read as
  permanently UNVERIFIED for this arm; the fix-for-a-defect conclusion rests on the accuracy contrast
  with head/tail controls, which is intact.

## 4. Not claimed

No cost saving, no paging/model-quality claim, no determinism. The free-tier call is a launch cost,
not a receipt. No re-score of Part B, no pooling. No plugin file touched; suite/gate not re-run (no code
change). Gateway holds 0.13.30 (verified earlier this session).

## 5. Owed

Owner ruling: which of the two options in §3. Review lane: verify + record this diagnostic.
