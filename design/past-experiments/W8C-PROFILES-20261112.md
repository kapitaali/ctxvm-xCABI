# W8C profile pairs — what exists, what each one reproduces, and when it goes

Written 2026-11-12, after cell-03 (paid) was booked. Rule of engagement: **exactly one arm pair per
prefix**, enforced by the runner's preflight count and by `tools/w8b-profiles.sh <prefix>`; the runner
never creates a profile.

## The pairs today

```
w8cn-naive   engine=compressor  meituan/longcat-2.5:free   control  — reproduces cell-02 (free)
w8cn-paged   engine=ctxvm       meituan/longcat-2.5:free   treatment, budget 60000
w8cp-naive   engine=compressor  openai/gpt-6-luna          control  — reproduces cell-03 (paid)
w8cp-paged   engine=ctxvm       openai/gpt-6-luna          treatment, budget 60000
```

Both pairs pass the check: exactly two profiles, differing only in `context.engine` and the paged
budget block. Four profiles exist because a subject change is a profile change — model and provider are
profile settings and cannot be overridden at resume — not because anything is provisioned per provider.

## Decision

**Keep both pairs until the W8 chunk closes.** Each pair is the reproduction path for one booked cell:
deleting `w8cn` now would leave cell-02's numbers pointing at a configuration that no longer exists,
which is exactly the failure the books are meant to prevent. When the chunk closes, delete `w8cn` in a
single commit and record in cell-02's card that its reproduction requires re-creating the pair — a
one-command copy from `w8cp` with the subject swapped back, not a rebuild.

Nothing else is provisioned. No per-model, per-key or per-day profiles; the key sync writes `.env` /
`auth.json` into the existing homes, it never creates a home.

## The installed plugin, cleaned in the same pass

The install at `~/.hermes/plugins/ctxvm-tracer/` still carried the old layout from before the flat-module
move: `live/`, an empty `src/`, `test_plugin.py`, `BUG_REPORT.md`, and `ctxvm.py`. Removed.

```
kept       __init__.py  context_engine.py  profile_policy.py  plugin.py  plugin.yaml
           uc1_handoff.py  uc_registry.py  uc2_forensics.py  uc3_planner.py
checked    the module loads and reports 0.13.2; one free prompt under w8cn-paged wrote a capture
           whose own sidecar attests profile w8cn-paged, arm paged, budget 60000
```

Two limits worth stating: the removal took the plugin's module set with it the first time (`live/` held
`uc_registry.py`, whose flat copy was missing from `src/`), which the load check caught immediately and
which is why the check exists; and the running gateway still holds **0.13.1** until it is restarted, so
the 0.13.2 behaviour (`evictedPages` in the sidecar) is not live yet.

## Not decided here

Whether the W8 chunk closes before or after the cache-stable decision is the owner's call. This note
only fixes the profile rule so the next pair cannot multiply homes again.
