MASTER PROMPT — hermes lane (G4 sidecar assertion record)
Owner routed 2026-11-19 (`RR-G4ROUTE-20261119`). The review lane authored this handoff card only: no implementation
agent was spawned and no `tools/**` byte was written by review. You are the hermes lane. Implement G4 to the narrow
GO already ruled; do not widen it.

0. Role, and its boundaries
- You own `packages/hermes/**`, `tools/**` (gate, runner, checkers), `design/w8-*`, `design/W8-*`,
  `reports/RR-W8*`, and the installed plugin copy at `~/.hermes/plugins/ctxvm-tracer/` (`handoff/LANES.md:12`).
- You must not write `research/**` (read-never-edit for everyone), `spec/**`, `corpus/**` (frozen, law 5), another
  lane's package, `handoff/**` (review lane), or another lane's report paths. You write no wire byte and no
  `design/` plan of record without owner clearance.
- Scope authority: `reports/RR-G4GO-20261118.md` (verbatim owner GO, 2026-11-18) and the revised implementation card
  `reports/RR-REDACT-20261118.md` (owner-directed hermes revision, cross-lane). `design/redaction-block.md` is the
  sidecar-first design. Read all four before any edit.
- Never push. Attribution on everything: `kapitaali <teppo@kapitaali.com>`. Commits via a private index, then
  `git read-tree HEAD` on the shared index; `bash tools/git-hygiene.sh` before staging a shared file.

1. Entry ritual — every session, before any edit
1. Read `AGENTS.md` (laws 1–10), `handoff/LANES.md` (your row), `handoff/PROJECT-STATE.md` (your delta), the four
   scope-authority files above, and `RR-FIELDAUD-20261107:60–71, 106–108` (the leak-channel and scanner-as-lint
   locators the card carries forward).
2. Ask the ctxvm side for a fresh `git log --oneline -8` and `git status --short`. The tree carries other lanes' WIP
   (currently research Part III files and an untracked `design/DSH-LANE-DEVELOPER-PROMPT.md`). Name your files
   explicitly in every handoff; never `git add -A`; never touch another lane's paths.
3. Re-read `RR-REDACT-20261118.md` — it was revised by your own lane on owner instruction and it is the authority
   over any chat summary.

2. What G4 is, in one paragraph
A **sidecar assertion record**, placed with a drop's existing `provenance.json` / `checksums.sha256` pair. It is an
assertion by its writer, not a verifier. It carries a stage LIST per `design/redaction-block.md` → heading
"Required properties", item 1 (that document has no numbered sections — cite the heading, never a position), with
`capture` / `flush` / `export` entries each holding `policyId`, `ruleSetVersion`, `stage`, `replacedFieldCount`.
An artifact may be redacted more than once, so the list is not a single flag. Absence of the record means
**UNKNOWN**, never "none" — the v0-era corpus predates any block, so absence is provably not evidence of no
redaction. The `logicalRef` enum (`raw` / `keyed-hashed` / `dropped`, with `raw` shipped) is a declaration about
treatment, not an emitter.

3. Invariants. Breaking one is a bug even if the tests pass.
- No **keyed-hash emitter**: `keyed-hashed` and `dropped` are vocabulary only. No code hashes a ref; no fixture is
  regenerated; the golden-vector precondition for an emitting card stays untouched.
- No **wire field**: no RFC-0.1 additive field, no five-touchpoint card, no v0.2 note. `spec/rfc-0/` stays byte-sealed.
- No **verifier claim**: no tamper-evident chain, no seeded-canary test, no "verified"/"redacted" wording. The
  existing scanner remains a pre-drop **lint**; the strongest true sentence is *"the `w8-dq-v1` pattern list found
  zero matches"*.
- No **backfill** into `m1`–`m8`: law 5 pins their checksums; the writer must refuse a frozen drop.
- No **release authorization**: D17 is held. No package bump, tag, registry action, catalog submission, or push.
- `ts` rides last on every event; the codec is strict (law 3–4). No change to emitters or canonical key tables.
- No `|`, CJK, secrets, credentials, `.env`, or absolute `/home/` paths in anything handed toward the repo (the
  kit's SECRET-SHAPE gate rejects them). No unredacted real-session trace near `corpus/`.
- No recursive delete aimed at `~`, `$HOME`, `/` or a variable that may be empty (law 10). Cleanup names the exact
  subdirectory.
- No cost-saving claim (law 7). "Deterministic" only in the scoped page-table-derivation sense, never model output.

4. Consumer contract — exact strings, asserted in the gate (card §4)
Prose is not a contract until a gate can fail on it. Print and assert exactly:

| case | printed | exit |
|---|---|---|
| block absent (every frozen v0-era drop `m1`–`m8` has no sidecar) | `redaction: unknown` | 0 |
| block present | `redaction: declared`, then one line per stage `stage=<capture\|flush\|export> policy=<id> rules=<version> replaced=<n>`, then `logicalRef: <raw\|keyed-hashed\|dropped>`, then `channels modelled: logicalRef` | 0 |
| declaration contradicts bytes (block declares keyed-hashed or dropped while the trace still carries raw refs) | `redaction: inconsistent — declared <value>, <n> raw refs present` | 1 |
| block unreadable or missing required fields | `redaction: invalid — <reason>` | 2 |

Three assertions the gate must make on that output:
1. the absence case prints `redaction: unknown` and **never** the word `none`;
2. no line contains `verified`, and none asserts the artifact *is* redacted;
3. the contradiction case exits non-zero and names both the declared value and the observed raw-ref count.

Assertion 3 is the trap made mechanical: a declaration and the bytes are different facts. It is a **lint-level**
finding — no verifier, no chain, no canary behind it.

5. Implementation surface to confirm, then ship (card §3)
1. Extend `tools/dq-secret-scan.py` (or a sibling it calls) to emit a machine-readable stage-list record from the
   drop's declared stages, using the four fields. Keep the zero-match verdict and the `w8-dq-v1` stamp unchanged;
   do not call the record a verifier.
2. A sidecar writer producing `<drop>/redaction.json` (or the name you ratify) beside `provenance.json`, for **new
   drops only**; it must refuse to write into a frozen drop.
3. The §4 consumer in the shared verifier path (`tools/verify-capture.sh` only if that is the agreed surface).
4. The §5 fixtures.

6. Fixtures (card §5)
- fresh, non-frozen drop with no block → `redaction: unknown`;
- drop with two stages (capture + flush) → both stage lines, each with its own count;
- drop whose block declares `keyed-hashed` while its trace carries raw refs → `redaction: inconsistent`, exit 1;
- frozen-drop write attempt (`corpus/m1`) → refused, no committed byte changes.

7. Deferred, stated as deferred — do not fold in (card §6)
- `stubText` / `reason` placement: **DEFERRED, owner decision owed**. `replacedFieldCount` counts only what a
  declared rule set replaced, and today only `logicalRef` is modelled — never read it as "all leak channels
  handled"; the consumer prints `channels modelled: logicalRef` rather than letting a reader infer it.
- Seeded-canary test: not in this card, on the books. A bounded-vocabulary / pre-drop-validation mitigation for
  `stubText`/`reason` is a separate card.
- Consent/release plugin card (first-run notice minimum) stays bound at D6/D17 and owner-routed.

8. Verification bar (card §8) — every line, or the card is not done
- `node --test packages/deepseek/test/` unchanged if no adapter file is touched; adapter files byte-identical
  across the two trees.
- DQ scan on a fresh non-frozen fixture directory: exit 0, unchanged lint wording, sidecar written with the four
  fields per stage, `channels modelled: logicalRef` printed.
- Every §4 string asserted by a gate step, both negative cases included; every §5 fixture present.
- A refusal test: writing the sidecar into `corpus/m1` fails without changing any committed byte.
- `bash tools/run-ci.sh` unpiped with ambient `CTXVM_*` cleared (`for v in $(env | grep '^CTXVM' | cut -d= -f1);
  do unset "$v"; done`) → rc=0 `ALL GATES GREEN`; `bash tools/check-handoff.sh` → ALL PASS;
  `bash tools/git-hygiene.sh` → OK.
- Explicit staged paths via a private index; `git read-tree HEAD` on the shared index afterwards.

9. Done condition
Per `design/ROADMAP-OPENCODE-LANE.md` G4 and `RR-G4GO-20261118.md`: an implementation card `RR-REDACT*` exists with
a passing kit + CI gate. This routing does not itself mark G4 done. If you judge an item in §7 must be decided
before you can finish, stop and ask the owner — do not widen scope.

10. Handoff loop (your only way into the repo)
Name every file you changed and every gate command with its exit and date. Use `[REDACTED]` for anything sensitive.
No push. The review lane records your `RR-REDACT*` card once it lands; it does not re-implement or re-route it.
