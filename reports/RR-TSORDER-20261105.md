# RR-TSORDER-20261105 — the test asserted an invariant the wire does not have

Card: corrective, same day. Trigger: the gate went red on a docs-only commit (W19, `7efd683`), in
`packages/node/test/tracer.test.ts:217`, on the assertion `tail snapshots are time-monotonic`.

## What failed

```
✖ ts rides LAST on every event, RFC 3339 UTC ms (RFC-0.1 §R4 / D9 default-ON)
  AssertionError: tail snapshots are time-monotonic
  actual  : 675,675,675,675,676,676,676,676
  expected: 675,675,676,676,675,675,676,676
```

Same values, different order: the observed tail is a two-stroke sawtooth.

## Root cause

`finish()` emits the tail grouped by event class — every `turn.render` for turns `0..N`, then every
`call.meta` — and both carry the stamp cached at that turn's `render()` call:

```ts
const now = tsEnabled ? stamp() : undefined;
turnStamps.push(now);
pendingMeta.push({ turn, ..., ts: now });   // same stamp as the render
```

So the tail's timestamp sequence is `[s0, s1, ..., sN, s0, s1, ..., sN]`. It is monotonic **only when
every stamp is equal**, which happens when the whole run fits inside one millisecond. On 2026-11-05
the run spanned 675→676 ms and the sawtooth appeared.

The grouping is deliberate: the tail is re-derived on every `finish()` so repeated flushes produce
identical bytes (D9 idempotency), and the event order is canonical by class and turn, which is what
replay reads. The wire is correct; the assertion was not.

## The 2026-11-03 fix was wrong in the same way

`8d0be1d` replaced one wrong assertion ("the whole stream is monotonic") with another ("the tail is
monotonic"). Both hold only under clock luck, and the commit message at the time called the failure
"very likely the 2026-11-03 flake". It was: the flake never went away, it went quiet. This card
corrects the record.

## The invariant the code has, now asserted in both lanes

1. The live prefix is stamped as events are pushed, so it is non-decreasing.
2. The tail is grouped by class: renders before metas, and only those two classes.
3. The turn stamps ascend with the turn index.
4. Each `call.meta` carries exactly its turn's `turn.render` stamp — the snapshot law that makes a
   re-flush byte-identical.

Assertion 4 is the one that actually protects D9; assertion 3 protects the ordering of turns. Neither
requires the file to be time-sorted, because it is not.

## The same assertion existed in the hermes lane

`packages/hermes/test/test_plugin.py` asserted `sorted(stamps) == stamps` across the whole stream. The
python `finish()` groups the tail identically, so the assertion was true by the same clock luck. Fixed
in the same card with the same four assertions, so the two lanes cannot disagree about the law.

## Red-before proof

```sh
# break the snapshot law: give call.meta a fresh stamp instead of the render's
perl -pi -e 's/providerUsage: orphan, ts: now/providerUsage: orphan, ts: stamp()/' packages/node/src/tracer.ts
node --test packages/node/test        # 19 pass, 2 fail
# restore
node --test packages/node/test        # 21 pass, 0 fail
```

The two failures are the stamp-equality assertion added here and the byte-stability check that
depends on it. Restoring the file restores 21/21.

## A process failure, recorded because it is the reason the red landed

The W19 commit went in with a red gate. The command was:

```sh
bash tools/run-ci.sh 2>&1 | tail -2 && git add ... && git commit ...
```

A pipeline returns the exit status of its **last** command, so `tail` reported success while the gate
had failed, and the `&&` chain ran. The rule this repo already states — never claim green without the
gate — was followed in letter and broken by the shell: the gate was run, its result was discarded.

Standing correction: run the gate unpiped, capture its status, and only then stage.

```sh
bash tools/run-ci.sh; rc=$?; if [ "$rc" -ne 0 ]; then exit "$rc"; fi
```

## Verification

| Check | Result |
|---|---|
| `node --test packages/node/test` | 21 pass, 0 fail |
| `python -m pytest packages/hermes -q` | 117 pass |
| `bash tools/run-ci.sh` (unpiped) | exit 0, `ALL GATES GREEN` |
| Red-before (fresh meta stamp) | 2 failures, restored to 21 pass |

## What this does not change

- No event was reordered, no field moved, no schema touched. The wire was right.
- No determinism claim changes: `finish()` remains byte-idempotent, and that is now tested by stamp
  equality rather than by an accidental property of millisecond resolution.
- Consumers that sort a tail by `ts` would see the sawtooth as out of order. None does today
  (`ctxvm stream` groups by session start, replay derives by turn), and the note is recorded so that a
  future consumer does not add one.
