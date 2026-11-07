# RR-FIELDAUD-20261107 — the §9.3 field-conduct audit Part II says is missing

Card: the white-paper lane's Part II draft (§9.3) asks for "a table of every field that can hold
user-derived content (page content, stub text, `logical_ref`, tool arguments, paths, model output) and
whether each is stored raw, hashed, or counted" and notes "This paper does not contain that audit." This
card contains it, mechanically: every wire field was extracted from the codec source
(`rust/crates/ctxvm-codec/src/model.rs`, the wire's authority; throwaway extractor in
`/tmp/opencode/w8chk/field_audit.py`, run twice, output byte-identical) and cross-checked against the
frozen corpus's 476 rows (eight drops, 17 `.jsonl` files). Read-only: no code, spec, design, or
runner-lane files touched.

## Inventory and conduct table

Wire names are camelCase (the codec's serde mapping); Rust names in parens when different. `S` = String
type, `O` = Option, `u64`s are counted.

**session.open** — `agentId` (S, **raw**; harness identity label), `model` (S, **raw**), `provider` (S,
**raw**), `budgetTokens` (u64, counted), `tokenizerId` (S, **raw**), `schemaVersion` (O&lt;S&gt;, raw-or-absent;
RFC-0.1 R0, checked literal "0.1"), `environmentId` (O&lt;S&gt;, **derived-hash** — `env-`+12 hex of SHA-256
over the credential-stripped git remote or worktree path; raw path/remote never carried; see the salt
note below), `ts` (O&lt;S&gt;, raw-or-absent; RFC-0.1 R4, D9 default-ON with the `CTXVM_TRACE_TS=0` per-trace
opt-out — read at flush time in the node adapters, once in the hermes plugin).

**page.declare** — `page` (PageRef, structured), `turn` (O&lt;u64&gt;, counted), `latencyMs` (O&lt;u64&gt;, counted),
`toolEffect` (O&lt;ToolEffect&gt;; RFC-0.1 R7 side-effect class, enum, v0.1-gated), `ts`.

**page.render** — `turn` (u64), `page` (PageId, structured), `mode` (RenderMode, enum: full|stub), `ts`.

**page.evict** — `turn` (u64), `page` (PageId), `stubText` (S, **raw** — harness-written recovery
text), `ts`.

**page.fault** — `turn` (u64), `page` (PageId), `source` (FaultSource, enum), `latencyMs` (O&lt;u64&gt;, counted),
`ts`.

**page.pin / page.unpin** — `page` (PageId), `reason` (S, **raw** free text), `ts`.

**turn.render** — `turn` (u64), `residentTokens`/`evictedTokens` (u64, counted), `headroom` (O&lt;u64&gt;, counted),
`prefix` (O&lt;PrefixCost&gt;, structured), `ts`.

**call.meta** — `turn` (u64), `provider` (S, **raw**), `cacheEstimate` (CacheEstimate, structured),
`latencyMs` (O&lt;u64&gt;, counted), `providerUsage` (O&lt;ProviderUsage&gt;, structured), `ts`.

**Structured children** (types are the audit's real content):
- `PageId`: `logicalRef` (S, **raw** — the leak channel), `contentHash` (S, **hashed**).
- `PageRef`: `id` (PageId), `kind` (PageKind, **enum**), `tokens` (u64, counted).
- `CacheEstimate`: `estHitTokens`/`estMissTokens` (u64, counted), `providerReported` (bool, flag).
- `ProviderUsage`: `inputTokens`/`outputTokens` (u64, counted), `cachedInputTokens` (O&lt;u64&gt;, counted).
- `PrefixCost`: `toolSchemas`/`messageCount`/`requestChars`/`systemPromptBytes`/`approxInputTokens`
  (O&lt;u64&gt;, counted), `source` (S, **enum-ish raw** — "measured" / backend label).

## Answer to §9.3, page by page

**Page content** — *not stored at any conduct level.* No event variant carries message/page content
bytes; pages travel as `(logicalRef, contentHash)` identity. This is what conditions Part II's
byte-replay claim (`RR-WP2REV-20261107`): the geometry replays from these events, the bytes ride the
sources the hashes point to.

**Stub text** — *raw, today.* `page.evict.stubText` embeds the page's own identity and recovery
arguments verbatim; the frozen fixture shows it: `[Paged out: read src/auth/session.ts (8.2k tok, 187
lines). Re-call read_file(path="src/auth/session.ts")...]` (m2–m5 fixture rows). If a page's tool name or
arguments are attacker-controlled, those bytes are inside trust-shaped harness text exactly as the draft's
§7.3 argues. Both of §7.3's mitigation shapes map onto this field: names from a closed vocabulary or
hashes inside `stubText`, plus the static property test (§12.4 Part 1), which needs no model spend.

**logical_ref + tool arguments + paths** — *raw, and the dominant surface.* Wire inventory in the frozen
corpus: 112 `tool:`-refs, 4 `file:`, 2 `summary:` — 112 references that embed tool names, arguments, and
paths raw (`tool:read_file(path="src/auth/session.ts")`). The draft's §7.3/§9.3 statement is confirmed by
the artifact. The other "160" rows in the census are the pre-sidecar v0.0 fixture shape, where `page`
carried kind/tokens without a ref at all (rows in m1, plus scattered renders/faults in m5–m8 with an
absent `logicalRef`) — so the audit should say: **the identity field is raw where present, and simply
absent in v0.0-era artifacts.** Presence-conditional audits are part of §9.3's "stage" idea.

**Model output** — *not stored raw.* Faults derive *from* outputs (the `identifier_scan` mechanism), but
what lands on the wire is the derived `logicalRef` and the enum `source`, not the output text. The raw
model-output surface therefore doesn't exist on the v0 wire; whatever a monitor reads comes through the
harness's own transcript, outside the trace.

**Everything else user-derived**: `reason` (pin/unpin) is raw free human text (`"explicit_api: hot
loop"` in the fixture) — same treatment as stub text: bounded vocabulary in front, or validate it in the
pre-drop scan.

## Hashed surfaces and the salt question the draft raises

One true hashing layer exists today: `contentHash` (sha256 of rendered content). The draft's §9.3
dictionary-attack caveat applies with force to *short, common* strings, and to anything a client can
enumerate; the corpus itself demonstrates the identity-only character: fixture content hashes like
`sha256:s1` and reused `sha256:9f2ac17d` across drops are fine for
*identity* but say nothing about uniqueness strength as a redaction boundary. `environmentId` is the
second sample: hashed by construction *and* salted by design — the salt is whatever the device/worktree
itself was, which is precisely why it *breaks joins across environments* (§9.3's warning) and why it must
never carry the raw remote or path.

## What gates exist today and what they cover the audit with

`tools/dq-secret-scan.py` runs pre-drop on this wire's bytes and covers: credential-key shapes
(`sk-`/AKIA/ghp_/gho_/pat_/xox), PEM headers, generic `api_key=` assignments, `Authorization:` and
bearer-token rows, `.env` assignments, **emails, absolute `/home/` paths, IPv4 addresses (private
included), and internal-TLD hostnames** — over the whole serialized line, which transitively covers
`logicalRef`, `stubText`, and `reason`. It exits 0/1/2, stamps its identity (scanner SHA-256 + scan-list
version + UTC date) into `provenance.json`, and never prints matched bytes (double-run verified; the
only between-run difference is `scanDate`). Measured this week on this repo's own workflow, the scanner
also catches *pattern descriptions*: the W8 lane's own LOG row quoting "emails, `/home/` paths" burns a
synthetic drop on `path.abs_home` (`RR-W8TPLCHK-20261107` §DQ) — pattern-shaped *prose* is a user-derived
leak channel that a field-level audit must include, and the fixture corpus has none.

This scanner is a pre-drop lint, not the draft's §9.4 verifier (no stage-list comparator, no
third-party standard). The audit keeps the distinction explicit so the paper's next draft can cite what
exists before negating it.

## Coverage completeness, mechanically

- Every corpus key across all 476 rows maps onto today's inventory (`corpus_keys_unmapped: []`), so
  byte-pinned fixtures and the current codec are in one vocabulary — no audit blind spots hidden in the
  frozen bytes.
- Six wire fields postdate the frozen corpus: `schemaVersion`, `environmentId`, `ts`, `toolEffect`,
  `providerUsage`, `prefix` (never_in_v0_corpus). All six carry the audit above; `ts` matters most for
  §9.3 because it is *new raw bytes on every row going forward*, though it is a capture clock, not
  content.
- Full extract in `/tmp/opencode/w8chk/field_audit.json` (throwaway; not committed), STABLE ×2.

## Recommendation for the paper (report-only; nothing proposed to the frozen spec)

1. Cite this audit instead of §9.3's "does not contain" sentence, with the page-content column as
   "absent by design, identity-only on the wire" — that presence keeps §2.2 conditioning honest at the
   same time.
2. Treat `stubText` and `reason` as the two raw free-text surfaces and adopt §7.3's two static
   mitigations for them; the first is a no-model-spend card against the repo's own stub renderer
   (§12.4 Part 1).
3. Keep the salt/join discussion grounded in `environmentId`: hashed + salted-by-worktree is exactly why
   the env key can't join across environments — the behavior it wants is already shipped and load-bearing.
4. The scanner coverage list is the concrete answer to "fields that leak, covered today": all surfaces
   named above the line the scanner patterns catch transitively; the residual classes are pattern-shaped
   prose (measured above) and anything DQ law hasn't named yet.

**Discipline**: read-only + reports; `spec/**`, `design/**`, `packages/**`, `benchmarks/w8/**`, `corpus/**`
untouched; nothing from this card stages outside `reports/**`.
