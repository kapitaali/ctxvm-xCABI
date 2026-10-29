# W12 Steps 0–1 — reconciliation and the zero-copy justification

**Status:** Analysis only. **No implementation, no `ctxvm_abi.h`, nothing published**
(the card's gate: implementation waits for W8 or D7). This note covers **Step 0**
(reconcile with the repo) and **Step 1** (justify before designing) of
`08.1-UPDATE-PROMPT.md` §W12.
**Date:** 2026-10-29.

---

## Step 0 — reconciliation: what "xCABI" means today, and the name collision

| Question | Answer (in-repo, locators) |
|---|---|
| Is there a `00-SPEC.md`? | **No.** The prompt's W12 Step 0 assumes one. The spec surface today is `02-xcabi-events-v0.md` (draft vocabulary) + `spec/rfc-0/RFC-0-xCABI.md` (normative, **sealed**) + `spec/rfc-0/x-cabi.schema-v0.json` (strict JSON Schema). |
| What does "xCABI" denote? | A **trace/interchange format**: pages, faults, renders, evictions, turn facts, call metadata — a JSONL event log with a JSON Schema and a replay contract. "ABI" in the name refers to an *exchange* ABI between harnesses, not a C calling convention. |
| Does W12's usage collide? | **Yes, directly.** W12 uses "xCABI" for a **C-ABI memory model** across a language-runtime boundary. Same name, different object. |
| Resolution taken here | W12 drafts use the provisional name **`ctxvm-rt` (runtime ABI layers, working name)** and never reuse "xCABI" for a C ABI. The trace format keeps the name. Flagged as part of **D7** ("how the runtime ABI relates to the sealed trace spec: same standard, a layered one, or a separate project"). |
| Consistency requirement | Any runtime ABI must be *consistent with* the sealed trace semantics: `page.declare` / `page.render` / `page.evict` / `page.fault` are the vocabulary the memory model would have to produce. It may not redefine them. |

Two consequences for anyone continuing this card:

1. Every W12 draft must cite `02-xcabi-events-v0.md` + `spec/rfc-0/`, not a
   non-existent `00-SPEC.md`.
2. If D7 answers "separate project", the provisional name becomes load-bearing and
   belongs in the name/trademark check that W10 owns.

---

## Step 1 — where zero-copy could matter (and the measurement that decided it)

### 1.1 The claim under test

The prompt asks for "a half-page analysis of where zero-copy actually matters. LLM
requests ultimately serialize to tokens and JSON over a network, so measure the
allocation/copy share of real session latency (from W1/W4 traces plus a
microbenchmark) against total latency… If the benefit is not measurable, say so and
shrink the ABI to the minimum needed for safe handles."

### 1.2 The measurement, and the honest result

**There is no real latency data in the corpus.** A census of every committed trace:

```
$ python3 -c "…call.meta latencyMs census over corpus/m*…"
call.meta total: 85        calls carrying latencyMs: 5
those 5 all live in corpus/m1  ← the SYNTHETIC seed drop (invented numbers)
real captures (m2, m4–m8): 0 latency measurements
```

So the first half of the prescribed measurement **cannot be performed**: no capture
records how long a provider call took. (`pre_api_request`/`post_api_request` carry
`api_duration` in the Hermes observer contract — see `packages/hermes/OBSERVABILITY.md`
§F3 — but the adapter does not record it, and no other emitter does either.)

What *can* be measured here is the cost of the data path ctxvm itself owns — the
canonicalisation and hashing that every page passes through, and the parse cost of
the log:

```
$ python3 … (median of 20 runs, this machine, 2026-10-29)
payload   canon+sha256 ms    throughput      tokens (apx4)
8 KB              0.046 ms   170 MB/s            2 048
50 KB             0.255 ms   192 MB/s           12 800
200 KB            1.070 ms   183 MB/s           51 200
1 MB              5.672 ms   176 MB/s          262 144

JSONL parse (corpus/m8/live-thrash.jsonl): 2 796 bytes in 0.067 ms
whole corpus: 17 files, 476 events, 4 ms
```

### 1.3 What those numbers mean

A 50 KB tool result — a large `read_file` — costs **0.26 ms** to canonicalise and
hash. For comparison, the *synthetic* latency samples in m1 range 860–2 440 ms; a
real provider call on the free tiers used for every live capture is of the same
order (hundreds of ms to seconds), and that is a statement about the model call, not
a measurement this repo has. Set against any of those, the data-path copy cost is
**≤ 0.1 % of a model round trip**, i.e. below the noise of what the harness can even
observe.

Conclusion, in the prompt's own terms: **the zero-copy benefit is not measurable with
this repo's data, so the ABI shrinks to the minimum needed for safe handles.** No
`ctxvm_arena_t`, no frame-appending API, no bytecode dispatch: those are designs in
search of a measured cost.

### 1.4 Where the benefit *would* have to show up (and why it is not testable here)

Zero-copy is a claim about **what happens inside one request**, not about the trace
log:

1. **Prefix/KV-cache reuse.** If a branch re-sends the same prefix, a provider's
   prefix cache (priced in `benchmarks/metrics/prices.json` v1 as
   `usdPer1mCachedRead` vs `usdPer1mInput`) makes the repeat cheap. A fork that
   changes the prefix forfeits that. This is a **net-token** effect, not a memcpy
   effect — the W3 price model already exists to price it; no experiment has been run.
2. **Large tool outputs crossing a language boundary.** Copying a 1 MB payload costs
   5.7 ms here; a model call costs ~200× that even measured against m1's *synthetic*
   1.24 s. Only a *local* inference loop with sub-10 ms per-request budgets could notice.
3. **Multi-branch sharing inside one process.** Real, but it is a property of a pager
   (v1 control plane, unbuilt and unmeasured — see `07-benchmarks-go-no-go.md`), not
   of the tracer.

None of the three is observable in a corpus of 17 traces that never page and never
record latency. The measured context-waste effect that *is* documented lives at the
request level (Pichay's 84.4× median re-mention amplification, arXiv 2603.09023 §5.1
— verified in `reports/RR-ADOPTIONINTAKE-20261029.md` §1), and it is an argument for
paging, not for a zero-copy C ABI.

### 1.5 Minimum ABI the evidence supports (stated, not designed)

Handles that are opaque, generation-tagged and cheap to validate; explicit ownership
with "nothing allocated on one side is freed on the other"; error codes instead of
unwinding. That is the whole of what the corpus can justify. Everything beyond it —
arena allocation, CoW branching, schema-by-handle dispatch — stays unbuilt until W8
produces a paging result or D7 authorises the design work.

---

## What this note deliberately does not do

- No header, no reference implementation, no benchmark harness for the ABI (the gate).
- No decision on D7 (owner-reserved: separate project / layered / same standard).
- No claim that zero-copy is worthless — only that **its benefit is unmeasured here**,
  and that a design without a measurement would be the exact failure mode the prompt
  warns about ("Do not claim zero-copy benefits without the Step 1 measurements").
