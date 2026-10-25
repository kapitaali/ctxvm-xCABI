# RR-M5-OPENSELF — first interactive self-capture: corpus drop M5 + the v2.1.4 flush-semantics erratum

**Card executed:** M5 · **Date:** 2026-10-25 · **Promotion of:** the UC3 live self-capture measured this session
**Scope:** `corpus/m5/` (new drop), manifest → 0.5.0, CI mirrors, `packages/opencode/live/ctxvm.ts` (instrumented adapter, lands with this card per the RR-HYG-1 handover note), `packages/opencode/live/README.md` (flush-semantics erratum), `00-README.md`, hub regen + re-baseline. Local-only, USD 0; witnesses under `/tmp/opencode/m5-self-capture/`.

## 1. What was blocked, and what closed it

The OpenCode *interactive* path was the last uncaptured harness shape: m2 captured scripted
one-shot CLI invocations (`opencode run --standalone --auto`, flush at process shutdown),
m4 captured a Hermes `/ctxvm-trace start|stop` window — but no long-running TUI session
had ever produced a trace. The morning attempt (2026-10-25) quit the TUI and flushed
*nothing*, undiagnosably because hooks fail silent.

This card turned the failure into a measured event and captured the queued session:

1. **Env forensics** (pre-during this session): the plugin loads in the **CLI/TUI
   process** — the TUI boot carries all 6 `CTXVM_*` capture vars; `opencode serve
   --service` carries none and can never flush anything. Consequences pinned: flush
   fires **only on graceful TUI exit** (SIGTERM → plugin cleanup); there is **no plugin
   hot-reload** (edits to `ctxvm.ts` are picked up next boot); a **hard kill discards the
   in-memory slice silently**.
2. **Instrumentation** (`packages/opencode/live/ctxvm.ts`, committed in this card): the
   adapter appends every hook fire and every flush attempt to
   `hooks-witness.log` inside `CTXVM_TRACE_DIR` (best-effort; witness failures
   swallowed by design). A missing flush is now diagnosable in one look.
3. **Stop-and-verify sequence** (user-run from a konsole): TUI first — it is the flush
   owner (SIGTERM runs plugin cleanup while the session is coherent) — then the
   background service, then the full verification stack. Witnessed:

```
2026-10-25T11:29:47 cleanup entered (plugin unload)
2026-10-25T11:29:47 cleanup finishAll -> 1 tracer(s)
2026-10-25T11:29:47 flush m5-self.jsonl bytes=16280 session=ses_e9c7bead…
2026-10-25T11:29:47 cleanup exit
```

## 2. The capture (what got promoted)

`m5-self-era1.jsonl` — the protected snapshot (later flushes overwrite the one
`CTXVM_TRACE_NAME`, so era snapshots are taken immediately) — became
`corpus/m5/opencode-live-session-01.jsonl` + `.meta.json`:

- **Census (80 events):** `session.open` 1 · `page.declare` 17 · `page.fault` 17 ·
  `page.render` 17 (all `mode: full`) · `turn.render` 14 · `call.meta` 14.
- **Pages:** 17 across three tool families — `shell` 12, `edit` 4, `write` 1 — 2,055
  declared tokens. Tool refs truncate argument JSON at 120 characters (RFC-0 §6).
- **The cold-entry double-row law, 17/17:** every novel page faults once
  (`source: identifier_scan`) in the completing call's turn and renders full on the next
  model request — declare → fault@t → full render@t+1. One context hook fires per
  **model request**, so this window's 14 contexts = 14 xCABI turns over the recorded
  work (RFC-0 §5 / T7 law, held at interactive scale).
- **Zero evictions by construction:** `residentTokens` constant 2,055 at all 14 turn
  boundaries, `headroom: 197945` of the declared 200000 budget, no `page.evict`.
  Per the BUDGETSWEEP reading rule, the honest policy reading: **NTR = 0.0** against
  the counterfactual-no-paging baseline, quoted beside the service metrics —
  rendered 28,770 tokens / est misses 2,055 / touchRatio 0.0714 / waste 0.9286 /
  whole-trace thrash 1.2143 (no window claim). This drop is a reference-string +
  flush-mechanics proof; pressure data remains the UC3 sweeps.
- **Honest miss shipped as-is:** `opencodeVersion: null` in the sidecar — the boot
  recipe omitted `CTXVM_OPENCODE_VERSION` (the adapter reads it from the process env at
  flush). The erratum adds the export to the recipe; the value is **not backfilled**.
- **No redaction, per the m2 precedent** (same harness family): refs are ≤120-char
  tool-argument snippets; pattern scan for secrets: 0 hits.

## 3. Verification stack (run on the snapshot, then via CI)

```
replay      → exit 0, divergences: [], 17 × faultOfResidentPage (the cold-entry
              shape itself — replay waste-class bookkeeping, not defects)
profile     → 80 events / 17 pages / 0 evictions / residentAtEnd 17 / faultless 0
export      → round-trip clean
metrics.py  → netTokens rendered 28,770 / est misses 2,055; NTR 0.0 (see reading rule)
schema      → PASS (135 checks on the drop alone; CI now sees 510 lines / 515 checks
              across 21 fixtures)
crates      → --test (adapter) 8/8 green incl. the instrumentation
```

## 4. Surfaces changed

| Where | Change |
|---|---|
| `corpus/m5/` | `opencode-live-session-01.jsonl` (+`.meta.json`, `provenance.json`, `README.md`, `checksums.sha256`) |
| `04-odps-dataproduct-corpus.yaml` | `RE-VALIDATED 2026-10-25` comment line; `latestDrop: corpus/m5`; `productVersion: 0.5.0`; description drops-list gains the m5 sentence |
| `tools/run-ci.sh` + `.github/workflows/ci.yml` | m5 fixture in the schema gate; new `(M5 OpenCode live)` checksum step (local mirror kept byte-equivalent in effect) |
| `00-README.md` | M5 milestone sentence + corpus-tree row (`v0.5.0`) |
| `hub/` | regen via `tools/build-hub.sh` + `hub.sha256` re-baseline (the script regenerates catalog/index but does **not** touch the checksums — that remains a card-by-card manual step, as at m4) |
| `packages/opencode/live/ctxvm.ts` | the diagnostic instrumentation (one new import; `wit()` lines at init/context/hooks/cleanup) — landed with this card, as pre-agreed in RR-HYG-1 §Handover |
| `packages/opencode/live/README.md` | **flush-semantics erratum (v2.1.4):** plugins live in the CLI/TUI process; flush only at graceful exit; no hot-reload; hard-kill loss is silent; one-name accumulation warning; interactive recipe gains `CTXVM_OPENCODE_VERSION` |

## 5. Rules held

- One card = one commit (this) + one ledger commit (LOG/board); `git status --porcelain`
  reviewed per stage; `research/*` and `~/.hermes` untouched; nothing PAT-related touched
  or stored.
- The m5 RR/README quote `NTR 0.0` only beside service metrics (RR-UC3-BUDGETSWEEP
  reading rule).
- `opencodeVersion: null` recorded honestly; recipe fixed forward in the erratum only.

## §Next

1. **Era-2 cash-in is live:** the current boot keeps capturing this session under the
   one name — if a second flush is wanted, snapshot `m5-self.jsonl` →
   `m5-self-era2.jsonl` immediately at the next turn before any other action.
2. The interactive recipe should grow an **automatic flush-verify step** (post-exit
   script checks witness + file presence; today's stack is a `/tmp` workbench, not
   repo tooling — a follow-up card could promote it into `tools/`).
3. Queue (unchanged order from prior RRs): windowed P-pathology reference sheet
   (POLICYSIM §Next 1), then T15 (Vercel adapter — needs a design pass).
