# RR-DECISIONS-20261031 — owner decision session: D8–D11 settled (emitter card, ts policy, productVersion, authorship)

**Follows:** `reports/RR-RFC01-20261030.md` §Open questions 1–3 (the emitter
blockers) · `reports/RR-RFC01E1-20261031.md` (the card the first three answers
gated — landed the same day) · `reports/RR-DECISIONS-20261030.md` (D1–D7;
numbering continues) · the authorship-anomaly finding from the RFC-0.1 landing
review (post-`d21bcb7`).
**Card:** owner decision session (structured question-and-answer,
recommendation-first options; answers recorded verbatim). Session 2026-10-31.
This is a **books-only** record: no code, schema, corpus, package, or
publication change (the emitter card D8 gated — `7aa6972` — was written in the
same session, before this record was filed; the answers themselves came first).

---

## 1. Decisions — all four settled; none outstanding

| ID | Question (source) | Owner answer | Consequence |
|---|---|---|---|
| D8 | Emitter card scope: one card or split (`RR-RFC01-20261030.md` Open question 1: the version switch is one line per adapter and immediately unblocks W2b) | **Split — version switch first** | Card 1 = the `schemaVersion: "0.1"` switch (rr-landed same session: `reports/RR-RFC01E1-20261031.md`): node tracer + hermes port, red-before proven, derived fixtures truth-up'd, driver guard, both gate mirrors extended. `providerUsage`/`ts`/`turn` follow as per-lane cards — W2b's wiring is next. |
| D9 | `ts` emission policy (`RR-RFC01-20261030.md` Open question 2 — ts changes the bytes of every future capture) | **Default ON, env opt-out** | When a lane's `ts` card lands, emitters stamp RFC-3339 UTC ms on every event by default; the per-trace opt-out `CTXVM_TRACE_TS=0` covers byte-stability needs. Each drop mints its own checksums at capture time, so default-on costs nothing at drop provenance; the sealed/frozen artifacts are untouched either way. |
| D10 | Manifest `productVersion` for the first v0.1 drop (`RR-RFC01-20261030.md` Open question 3) | **Bump to "0.1" at the first v0.1 drop** | The first drop containing v0.1 traces gets `manifest.yaml` `productVersion: "0.1"` + hub regen; v0-era drop manifests stay frozen. This is an in-repo version bookkeeping bump — tags/registry publishes/index submissions stay gated on W8 (D6). |
| D11 | The three pushed commits `36cec7c` / `f0f2710` / `d21bcb7` are signed `ctxvm <ctxvm@local>` instead of the law identity `kapitaali <teppo@kapitaali.com>` (content verified green: runs `41091691596`, `41092591998`, both 4/4) | **Record in books — no history rewrite** | Deviation recorded here; pushed main history is never rewritten. Root cause: a transient local identity override set by the (context-lost) RFC-0.1 continuation session — the global gitconfig was always law-correct; the local override was found and removed the same day it was diagnosed (`git config --local` now carries NO `user.*` keys). Standing laws: commits sign `kapitaali <teppo@kapitaali.com>`; any future mis-signed commit is recorded, never force-pushed. First post-deviation commit `7aa6972` (RFC-0.1 emitter card 1) is law-signed and verified. |

## 2. Notices recorded in the same session

- **Umpire cross-repo tail (still open, owner-coordinated):** the fixture
  regeneration card (four triplets → `intentional_rerun`; refs/hashes/token
  counts unchanged, page-table baselines change only in fault `source`) cannot
  start while `~/Documents/umpire/` carries a dirty worktree
  (`M .gitignore`, `M README-MCP.md`; untracked `hermes/`, `research/`,
  `.open-data-products/`). Owner option on record: work it in a fresh clone and
  hand the owner the patch, or the owner tidies first; its push uses its own
  PAT-run law. Only the owner may commit/stash the dirty files.
- **XERJ standing item unchanged:** README `pending — UNVERIFIED` until a live
  Hub listing exists.
- **Donation policy unchanged:** all donations → compute + development; spend
  recorded in reports (address validated + public in README).
