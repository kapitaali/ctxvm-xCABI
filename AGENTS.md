# AGENTS.md — ctxvm / xCABI

Instructions for any agent working in this repository. Read this first, then `00-README.md`, then
`08-HANDOFF.md` §0–§4 (rules of engagement). `08.1-UPDATE-PROMPT.md` holds the workstreams (W1–W16)
and the owner's decisions; `design/` holds plans of record per card.

## 1. What this repo is

ctxvm is a virtual-memory manager for agent context, and **xCABI** is the trace standard it emits.
A trace is a JSONL file: one event object per line, nine v0 verbs plus RFC-0.1 additive fields.
`ctxvm replay` re-derives the page table from a trace; the Rust core is the authority.

## 2. The one command that decides whether you are done

```
bash tools/run-ci.sh          # prints "ALL GATES GREEN" or fails
```

It mirrors `.github/workflows/ci.yml` step for step (rust → typescript + python → schema/corpus/export
→ hub). Do not claim a change works without it. Two companion tools:

- `python3 tools/ci-rehearsal.py` — clones the committed tree into a temp dir and runs each job's
  `run:` steps in order. Catches the case where the gate is green only because of uncommitted state.
- `bash tools/check-node-build.sh` — builds `packages/node/dist` and proves it emits the same 16
  events as the sources.

A red gate is never "pre-existing". Find out what changed. Since 2026-11-03 every step runs through
`run_step`, so a red gate prints the failing step's name, the last 40 lines of its output, and the path
of the kept log. If you ever see a bare exit code with no step name, you are running a stale copy of
`tools/run-ci.sh`, not a mysterious failure.

## 3. Layout

```
rust/crates/ctxvm-codec      wire model + strict JSONL codec (allowlist, no silent drops)
rust/crates/ctxvm-core       replay, page table, diff, profile, export
rust/crates/ctxvm-conformance  CLI binaries + conformance vectors (the byte authority)
rust/crates/ctxvm-tokenizer  tokenizer (tiktoken feature)
packages/node                @ctxvm/node — TS tracer mirroring the Rust model
packages/opencode            OpenCode adapter (hook → event mapping)
packages/ai-sdk              ai-sdk middleware adapter
packages/hermes              Hermes Agent plugin (Python) + live adapter
packages/py                  Python binding
spec/rfc-0                    sealed v0 schema + validator
spec/rfc-0.1                  RFC-0.1 schema, validator, normative text
corpus/m1..m8                frozen trace drops with checksums
benchmarks/metrics           metrics suite + policy simulator
hub/                         ODPS hub artefacts (byte-identity checked)
tools/                       run-ci.sh, rehearsal, export round-trip, node-build parity
reports/                     RR-<CARD>-<date>.md, LOG.md (append-only), RR-DAY-<date>.md
```

## 4. Laws. Breaking one is a bug even if the tests pass.

1. **RFC-0 is sealed.** `spec/rfc-0/` and the v0 validator do not change. The v0 schema must keep
   rejecting every v0.1-only line, and the frozen fixtures keep their committed bytes.
2. **RFC-0.1 changes are additive and version-gated.** A new field needs all five touchpoints:
   Rust model (declared **before `ts`**), the codec `FIELD_ALLOWLIST`, the v0.1 schema branch
   (`additionalProperties: false`), a `check_version` gate, and a validator negative. Then the
   conformance vector.
3. **`ts` rides LAST on every event.** Emitters, the Rust struct order, and the canonical key
   tables all agree on this. A field appended after `ts` breaks byte-identity in ways that look
   unrelated.
4. **The codec is strict on purpose.** Unknown `type` tags, unknown fields and float token counts are
   hard errors — serde would silently rewrite traces otherwise. Never relax this to make a test pass.
5. **Corpus drops (m1–m8) are frozen.** `corpus/*/checksums.sha256` pins their bytes.
   `packages/hermes/test/generate_traces.py --force` overwrites two of them and orphans the
   checksums — do not use `--force`; the live fixture regenerates without it.
6. **Emitter-produced fixtures are regenerated, never hand-edited:** `npm run gen` in
   `packages/node`, `packages/opencode`, `packages/ai-sdk`, or
   `python packages/hermes/test/generate_traces.py`. `test/gen-fixture.ts` wipes every `CTXVM_*`
   var, so any var its replay pin needs must be set again after the wipe.
7. **No cost-saving claim.** No token saving has been measured on our data. W13–W16 make cost
   *measurable*; they do not reduce it. The 18.4–30.9% in arXiv:2610.22732v1 belongs to an external
   controller that does not use ctxvm.
8. **No "deterministic" without scope.** We prove page-table derivation determinism (byte-identical
   derivation across machines), never model-output determinism.
9. **Capture is default-on and private.** Traces land in
   `${XDG_STATE_HOME:-~/.local/state}/ctxvm/traces` at `0700`. Real-session traces never leave the
   machine and never enter `corpus/` unredacted.

## 5. Verification culture

- Every number in a doc must be reproducible by a command in this repo. State sample size, model,
  machine, seed and interval where they apply.
- External claims carry a locator at first mention; anything unverified is marked `UNVERIFIED`, never
  asserted.
- Negative results and failures get the same prominence as successes. A "no-go" is a publishable
  outcome.
- Prefer one measured number over three adjectives. No marketing language.

## 6. Recording work

Every card produces:

1. `reports/RR-<CARD>-<date>.md` — what was done, repro commands, numbers with intervals,
   limitations, deviations, open questions.
2. A row appended to `reports/LOG.md` (append-only; never rewrite existing rows).
3. A section in `reports/RR-DAY-<date>.md`, and a day-close line in `08-HANDOFF.md` when the day ends.

Plans of record live in `design/` (e.g. `design/W15-tool-effect.md`). If a chat summary and a file
disagree, the file wins.

## 7. Git and secrets

- **Never push.** The owner pushes.
- Never commit credentials, tokens, `.env` files, or unredacted traces. Use `[REDACTED]`.
- Commits are attributed `kapitaali <teppo@kapitaali.com>`.
- Do not stage unrelated work in progress — another agent may own it. Check `git status` and
  `git log --oneline -5` before staging anything.
- Note that `git rev-list --count origin/main..HEAD` reads the *local* tracking ref, which goes stale
  here. Use `git ls-remote --heads origin` to see the real remote head.

## 8. Test commands, by package

```
( cd rust && cargo test )                    rust, all crates (no root Cargo.toml)
node --test packages/node/test               @ctxvm/node
node --test packages/opencode/test           OpenCode adapter
node --test packages/ai-sdk/test             ai-sdk adapter
python -m pytest packages/hermes -q          Hermes plugin + live adapter
python -m pytest packages/py -q              Python binding
venvs/odps/bin/python -m pytest benchmarks/metrics -q
python3 spec/rfc-0/validate_schema.py <fixtures...>
python3 spec/rfc-0.1/validate_schema_v0_1.py <vectors...>
```

The gate prints the authoritative totals; do not hardcode counts in docs.

## 9. Current state (keep this section current)

- The **committed** HEAD is green and mirrors `ci.yml`. RFC-0.1 is landed; the sealed v0 boundary
  is intact. A dirty tree may be another agent's work in progress — check `git status` before
  concluding that a failing test is yours.
- Landed through 2026-11-07: W13 (`turn.render.prefix`), W14 (environment key), W15 (`toolEffect`
  side-effect classes), W17 (coverage-manifest sidecar + checker), W18 (monitor replay tier 1),
  W21 (collide-proof trace filenames), W10 node build + CI wiring, and the RFC-0.1 emitter chain
  (`schemaVersion`, `providerUsage`, `ts` on all four lanes). W16 (causal edges), W19 (tier-2
  interventions) and W20 (trace-surface extensions) are design notes only, owner-gated. The §5
  card board is fully statused; the remaining open work is owner-gated: W8 reopen (ruled FAILED
  2026-11-07; reopen conditions in RR-W8CHUNK-20261107-2 §12 + `design/W8-PROMPT-SLICE.md`), W12
  beyond Steps 0–1 (D7 hold), publication (D17). The OTLP exporter is promoted to the supported
  path with a field-set drift guard (D3-c, 2026-11-08, `reports/RR-D3COTEL-20261108.md`).
- Review round: reviewer Packet 1 answered 2026-11-08 (D13 recorded in `handoff/QUESTIONS.md`);
  P2/P3 pending. The session-continuity kit lives in `handoff/`; `bash tools/check-handoff.sh`
  must stay green.
- `packages/hermes` capture is default-on at plugin 0.10.x; the installed copy lives in
  `~/.hermes/plugins/ctxvm-tracer/` and needs a gateway restart to take effect.
