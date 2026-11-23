# RR-PARTC-REVIEW-20261123 — verified: Part C stub seam landed, off by default under the gateway's own interpreter

Review lane, verify-then-record. Subject: `5f96402` (plugin seam) + `c32bb90` (PROJECT-STATE delta), card
`reports/RR-PARTC-IMPL-20261123.md`, under the Part C authorization (`RR-PARTC-AUTH`). Date 2026-11-23. $0, no
model call, no gateway action by this lane.

## 1. Verified from disk

| claim | check | result |
|---|---|---|
| version bumped both places | grep repo + installed `__init__.py` | both `PLUGIN_VERSION = "0.13.30"` |
| sync | `bash tools/sync-plugin.sh --check` | repo/installed/manifest all **0.13.30**, installed load check OK, "gateway pid 107811 started after these files were written; it holds this build" |
| gateway live | `ps -p 107811` | started **2026-11-23 19:03:14**; interpreter is the gateway's bundled python-3.14.9 |
| seam in code | grep `context_engine.py` | `_stub_dropped` default `off` (`:338–341`), call-time adoption from policy (`:517–519`), plan attestation `stubDropped`/`stubCount` (`:581–582`), stub emission at `:992,1021–1041` ("re-run to restore", tool+args only) |
| card exists | `ls reports/RR-PARTC-IMPL-20261123.md` | present (3,656 B) |

## 2. The decisive condition — off by default, verified under the gateway's interpreter

Ran the **installed 0.13.30** plugin under the **gateway's own bundled python** with a minimal host-ABC stub:
- profile with **no** `stubDropped` setting → `stubDropped='off'`, source `default`; engine built from it →
  `_stub_dropped='off'`.
- profile with `stubDropped: recoverable` → `'recoverable'`, source `settings`.

So the opt-in channel works and **nothing ambient turns the stub on in real sessions** — the condition of the
authorization (D6/D14 consent, D17 held) is satisfied by the shipped build. No API keys or credential values were
read or recorded.

## 3. No real capture attests it yet — recorded, not assumed

The newest sidecars on disk are still pre-restart 0.13.29; this session has not full-flushed, so there is no 0.13.30
capture carrying `plugin.stubDropped` yet. The default-off claim rests on the interpreter probe above (shipped code),
not on a real capture. A 0.13.30 sidecar should appear on the next flush; until then, "captures attest the setting"
is verified in code/tests, not in a live artifact. This is recorded as an evidence gap, not papered over.

## 4. Scope and owed

The seam is plugin-side only (`packages/hermes/**`, hermes lane); I wrote none of it. Part B's result is untouched —
no re-score, no pooling. **Still owed:** experiment lane builds/runs the opt-in stub arm (8 sessions, frozen bank/
scorer/profiles, re-read readout from trace tool calls); any real-session default-off attestation on the next flush.
No D17 release action, registry/catalog, default-on change, or push.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.
