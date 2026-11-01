# RR-20261101 — W10 rider: the `engines` floor verified — sources 22.6.0 real; the dist artifact runs lower

**Card:** the W10 build card's open rider ("A compiled tarball would allow a lower
floor, but no older Node available to test a lower pin" — `reports/
RR-W10BUILD-20261031.md` §deviations). This card **verifies the pinned floor AND
measures below it**, with real older node binaries. No `engines` change (the
field is publish-adjacent; publishing stays gated on W8 / D6). **Date:**
2026-11-01.

## 1. What was tested (real binaries, exact versions)

| Node | Source | Suite result |
|---|---|---|
| 26.13.0 | `https://nodejs.org/dist/latest-v26.x/` (released 2026-10-28; `dist/index.json`) | `node --test test/` → 20/20 (the standing invocation) |
| **22.6.0(the pinned floor value)** | `https://nodejs.org/dist/v22.6.0/node-v22.6.0-linux-x64.tar.gz` | `node --experimental-strip-types --test test/tracer.test.ts` → **20/20** |
| 20.20.2 | `https://nodejs.org/dist/latest-v20.x/` | sources do not run (no type-stripping at all), dist consumer green (below) |

## 2. The two facts that hang on the pinned floor (both observed, neither theory)

1. **Sources NEED the floor as pinned — but the invocation differs by version.**
   At 22.6.0 the ts suite is green with **the explicit
   `--experimental-strip-types` flag** (strip-types is default-on only from
   later majors — node 26 does not need it) AND with **file arguments**
   (`node --test test/tracer.test.ts`). The REPO'S OWN invocation form,
   `node --test test/` (a directory argument), fails at 22.6.0 with
   `ERR_MODULE_NOT_FOUND` ("Cannot find module '…/test'") — the test-runner
   directory-argument feature does not exist on that node. An invocation
   surface fact, not an artifact defect: no consumer of the published package
   ever runs `node --test`. The `engines: node → ">=22.6.0"` pin is REAL for
   sources as stated.
2. **The published artifact runs LOWER than the pin.** A dist-only consumer
   (import `dist/index.js` directly, one echo trace, `CTXVM_TRACE_TS=0`) is
   **byte-identical across 20.20.2 / 22.6.0 / 26.13.0**
   (sha256 `40a9618f60bd…` all three) — so the shipped JS does not need
   strip-types and supports a floor BELOW `22.6.0`; node 20 LTS is observed
   green. Candidate for a future publish-time decision (D6): the engines
   value could be lowered toward the artifact's true floor at publish time;
   today the README/quickstart-facing statement is exactly what the field
   says, and no test required it otherwise.

## 3. Consequences recorded (decision stays D6/owner at publish time)

- **Verified floor is honest today; no change made.** The W10 card's UNVERIFIED
  rider closes as: the pin is verified REAL for sources; the artifact supports
  more than the pin; whether to lower `engines` at publish is a package-metadata
  decision gated with publishing.
- **One runner-normalization option for the future record** (not landed here,
  flagged for a next CI-adjacent card if someone wants the repo runnable at
  literally 22.6.0): the suite invocation could take file args with a
  version-conditional flag (e.g., `node --test test/*.test.ts` +
  `NODE_OPTIONS=--experimental-strip-types` on <23). Not a defect today: node 26
  runs everything as the ship state.

## 4. Repro (all evidence local; the event hashes are the unit of comparison)

```
cd /tmp/opencode && cat > dist-consumer.mjs <<'EOF'
import { createTrace } from '<repo>/packages/node/dist/index.js';
const t = createTrace({ agentId: 'floor-check', model: 'm', provider: 'p',
                        budgetTokens: 5000, tokenizerId: 'apx4-char' });
t.page({ ref: 'file:a.ts', kind: 'file', content: 'const A = 1;\n' });
t.render();
t.render();
process.stdout.write(t.finish().jsonl);
EOF
CTXVM_TRACE_TS=0 <node20bin>/node dist-consumer.mjs | sha256sum   # 40a9618f60bd…
CTXVM_TRACE_TS=0 <node26bin>/node dist-consumer.mjs | sha256sum   # same
# sources at the pinned floor:
<node22bin>/node --experimental-strip-types --test test/tracer.test.ts   # 20/20
<node22bin>/node --test test/                                            # fails (dir-args absent)
```

## 5. Limitations

- The floor test compares one trace's bytes; it exercises consumed exported
  surface exactly to the echo-trace depth (declaration + two renders + flush),
  not every exported API function. The equality claim is scoped to the observed
  shape.
- Node versions below 20 are untouched (nothing measured, no claim made).
- The dist build ran once on node 26 (the ship state) — the three-node equality
  is a CONSUMER statement for the existing bytes, not a rebuild-on-each-node
  statement.

## 6. Deviations

None. Read + shell session end to end; the only writes are books and this
report; no package.json/metadata touched (D6/D5 discipline).
