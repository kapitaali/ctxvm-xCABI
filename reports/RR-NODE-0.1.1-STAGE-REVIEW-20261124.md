# RR-NODE-0.1.1-STAGE-REVIEW-20261124 — verified: staged @ctxvm/node 0.1.1 + DSH passive-stub integration pass

Review lane, verify-then-record. Subject: the DSH workspace staging at
`~/Documents/deepseek-harness/default-workspace/ctxvm-dsh-scaffold/staging/ctxvm` and the installed DSH tree at
`~/Apps/deepseek-harness`. Date 2026-11-24. $0, no model call, no publish, no push.

## 1. Where 0.1.1 actually is

The public npm registry still returns **404** for `@ctxvm/node@0.1.1`, and the ctxvm repo package remains
`0.1.0`. The completed 0.1.1 artifact is in the DSH staging tree:

- `~/Documents/deepseek-harness/default-workspace/ctxvm-dsh-scaffold/staging/ctxvm/packages/node/package.json`
  → `name: @ctxvm/node`, `version: 0.1.1`, public `publishConfig`.
- Staging card: `.../staging/ctxvm/reports/RR-DSHSTUB-PASSIVE-20261124.md`.
- The staging manifest overlays these files onto the ctxvm repo; it is not itself a git checkout.

The installed app tree is **not** on 0.1.1 yet:
`~/Apps/deepseek-harness/packages/deepseek/package.json` still declares `"@ctxvm/node": "file:../node"`, and
`packages/deepseek/node_modules/@ctxvm/node` is a symlink to `/home/theb/Documents/ctxvm/packages/node`
(0.1.0). The staged open-dsh copy already declares the exact external dependency `"@ctxvm/node": "0.1.1"`.

## 2. Verification performed on the staged 0.1.1 code

I copied the staging tree to `/tmp/opencode/ctxvm-node-0.1.1-stage`, supplied the repo's existing package
`LICENSE` and dev `node_modules` (the staging subset intentionally omits both), and changed nothing in either DSH
directory.

| check | command / surface | result |
|---|---|---|
| node unit suite | `node --test test/`, `CTXVM_*` cleared | **30 passed, 0 failed** |
| build | `npm run build --silent` | **rc=0** |
| source/dist parity | staged `tools/check-node-build.sh` | **21 events byte-identical**, dist imports resolve |
| clean consumer install | `npm pack` → install tarball into empty temp project | **@ctxvm/node@0.1.1**, zero runtime deps, compiled dist only |
| consumer runtime | mirror API + new `stub()` API | **9-event mirror + 10-event stub trace pass** |
| stub semantics | exact PageId/text/turn; evict→stub-render order; `ts` last; restore totals | **pass**: turn 0 `[resident=0, evicted=10]`, turn 1 `[resident=10, evicted=0]` |
| consumer types | strict `tsc --noEmit` against installed package | **rc=0** |
| schema | repo v0.1 validator over both traces | **all checks passed** |
| replay | Rust replay over both traces | mirror `divergences=[]`; stub `divergences=[]`, `violations=[]` |
| DSH adapter | staged `tools/ci-deepseek.sh` with external 0.1.1 tarball | **22 passed, 0 failed, 1 named skip** |
| DSH checker | `tools/test_coverage_check.py` | **13 passed** |

The mirror smoke deliberately recalls resident pages, so its two `faultOfResidentPage` violations are expected and
do not make replay fail. The stub trace is clean.

## 3. Implementation checks

- `Tracer.stub()` accepts `{ref, contentHash?, stubText, turn?}`; unknown PageId / empty text / invalid turn returns
  false with no half-pair.
- It emits one atomic `page.evict` + `page.render(mode="stub")` pair for the exact original PageId and visibility
  turn; `stubText` is byte-preserved and `ts` is last.
- Ref-only calls select the first declared PageId; exact `contentHash` selects historical versions.
- A superseded same-turn full render is retired before the stub pair, keeping Rust's final mode schedule consistent.
- Re-fetch after stub schedules full restoration from the next turn; per-turn resident/evicted totals follow the
  effective schedule. Mirror-only output remains covered by source/dist parity.

## 4. Packaging / rollout notes

- The staging subset has no `LICENSE` and no `node_modules`; do **not** publish directly from that folder. The
  intended path is to apply `manifest.txt` onto the ctxvm repo (where `packages/node/LICENSE` already exists), run
  the gates, then publish. My temp overlay mirrors that path.
- Public npm is still 404; the staging card correctly says publish is an owner action and must happen before the
  DSH package can install exact `0.1.1`.
- `~/Apps/deepseek-harness` still runs 0.1.0 through the repo symlink. After publish/landing, its dependency must
  move to exact `0.1.1`; the staged open-dsh manifest already shows the intended shape.
- No source file in `packages/**`, `tools/**`, `research/**`, or either DSH directory was modified by review.

## 5. Re-run command

The consumer harness used for this review is `/tmp/opencode/test-ctxvm-node-package.sh`. Once the real artifact
exists:

```sh
bash /tmp/opencode/test-ctxvm-node-package.sh @ctxvm/node@0.1.1
# or
bash /tmp/opencode/test-ctxvm-node-package.sh /path/to/ctxvm-node-0.1.1.tgz
```

It checks tarball surface, clean install, runtime mirror + stub APIs, strict types, v0.1 schema, and Rust replay.

## 6. Scope / claim ceiling

Passive stub wire and DSH integration only. No active paging, cost, quality, determinism, availability, or
redaction claim. No live stub-arm attestation; the accepted Part C gap is unchanged. No model call, spend,
default-on, D17 action, publish, commit of DSH files, or push.

## 7. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261124.md`.
