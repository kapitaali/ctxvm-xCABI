# RR-W22-LOCAL-NODE-REVIEW-20261125 — verified: repo-local tracer installs work; shadow fix is live at 0.13.35

Review lane, verify-then-record. Subject: ctxvm `ffe8ff6`, open-dsh `30af9423a3`, and the operator restart
to Hermes 0.13.35. Date 2026-11-25. No npm publish, registry lookup, model call, or push.

## 1. Owner ruling implemented

The DSH adapter now consumes `@ctxvm/node@0.1.1` from the ctxvm checkout:

- ctxvm: `packages/deepseek/package.json` → `file:../node`
- open-dsh: `packages/deepseek/package.json` → `file:../../../../Documents/ctxvm/packages/node`
- both READMEs require a local node-package build and state that npm publish is unnecessary
- `tools/ci-deepseek.sh` still builds/packs the tracer locally; no registry lookup

This matches the owner ruling: **do not publish `@ctxvm/node`; keep it in the ctxvm repository.**

## 2. Install/runtime verification

| check | result |
|---|---|
| ctxvm adapter install | `npm install` resolved local `@ctxvm/node` **0.1.1**, rc=0, 0 vulnerabilities |
| open-dsh adapter install | rc=0, 0 vulnerabilities; `node_modules/@ctxvm/node` resolves to `/home/theb/Documents/ctxvm/packages/node` 0.1.1 |
| node suite | **30 passed** |
| ctxvm adapter suite | **35 passed, 0 failed, 1 named skip** |
| open-dsh adapter suite | **35 passed, 0 failed, 1 named skip** |
| ctxvm `ci-deepseek.sh` | **rc=0**, 35 passing |
| open-dsh typecheck | **rc=0** with temporary workspace peer links; links removed |
| full ctxvm CI | **rc=0 ALL GATES GREEN** |

The first open-dsh typecheck attempt again failed only because the checkout lacked peer links; temporary links to
the existing workspace packages made it pass. No source or manifest change was needed.

## 3. Shadow fix is live

- `sync-plugin.sh --check`: repo/installed/manifest **0.13.35**, load OK.
- Gateway pid **154985**, started **19:50:47**, after the 0.13.35 files were written; sync confirms it holds the
  build.
- Under the gateway's own interpreter, the installed `shadow_schema.py` validates the versioned fixture.
- Newest real sidecars are still from **19:36:48 on 0.13.33**, before the restart. No post-restart flush and no
  `w8-shadow/ctxvm-shadow/selection.jsonl` record exists yet.

So the fix is live, but **real shadow-data attestation awaits the first `w8-shadow` session flush**.

## 4. Scope / claim ceiling

- Mirror remains default; no real profile was enabled by review.
- Shadow collection is accepted only on `w8-shadow` after a real flush, with hashed/private records and
  offline-only candidate pins.
- No causal, cost-saving, paging-quality, model-quality, determinism, availability, or redaction claim.
- No npm publish, registry action, remote model call, spend, or push.

## 5. Applied

This card, an append-only LOG row (four pipes), a day-file section, and PROJECT-STATE version/live updates.
