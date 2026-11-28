# SHADOW-BATCH-FIXTURE-PROPOSAL-20261128 — draft fixtures and prompts for research ratification

Status: **DRAFT — RESEARCH/EXPERIMENT RATIFICATION REQUIRED — NOT AUTHORIZED FOR LIVE COLLECTION.**
Date: 2026-11-28
Authority: `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md` and the operator's 2026-11-28
instruction to draft the missing freeze for research approval.

This proposal does not replace the research-owned freeze. No model call, session creation, gateway/profile
change, restart, pin activation, publish, or push is authorized by this document.

## 1. Draft artifact

The private draft root is named `shadow-fixture-draft-20261128-v1` under the operator's ctxvm state
directory. It contains:

```text
generate.py
manifest.json
prompts.json
metadata.json
checksums.sha256
pressure/
  large-a.md
  large-b.md
  tail-1.md
  tail-2.md
  tail-3.md
dependency/
  A.md
  B.md
  C.md
  tail.md
```

Directory mode is `0700`; every file is `0600`. The generator is deterministic with seed `20261128`.
The draft manifest uses the collector's required `ctxvm-shadow-fixtures/v1` schema.

- Manifest SHA-256: `202b9468ffa53301e7b56e29a2df92a3074c47ecb1a5f4164c50f820acdbc735`
- Generator SHA-256: `3c72e83e79e53374574df24889c32cef956874d4789cf17f517983663782f541`
- `sha256sum -c checksums.sha256`: all 12 entries pass.
- `tools/collect-shadow.py::load_fixtures()`: all three shapes validate.

## 2. Frozen candidate files

| workspace | file | bytes | SHA-256 |
|---|---|---:|---|
| pressure | `large-a.md` | 57,600 | `802e5ab5795fc2c299f1f956bdecdfc43c47e6ecacfe10fb21f866f891e9f0b7` |
| pressure | `large-b.md` | 57,600 | `dc5b35611f3b0b83b71b60c2361b022f1032e2670cb4f43cfa1578dc048527ef` |
| pressure | `tail-1.md` | 192 | `59bc472d1f1ea09ab7ff8122ea5df4c8fe79a884a18dbbaad70b15fa06a78991` |
| pressure | `tail-2.md` | 192 | `8a7e058749ee86b0107263774bb56788efe8de8b094c809fb18bc1e7c02fd5dc` |
| pressure | `tail-3.md` | 192 | `344cf804b418a563d281cb4b423cc438b0e0a3010885ebf43e5379b1e76bec03` |
| dependency | `A.md` | 57,600 | `01b0bf472e353c8879af93a3c7fc2df25ae37b71bce4291725cd9f06f1706595` |
| dependency | `B.md` | 57,600 | `5bcfa2cb2a93d4c814863fb43ce1c5d9d8185914bb37e16afa82e287c492c147` |
| dependency | `C.md` | 28,800 | `1eecca26c6ada026249cb1b43a9d482789640789f54436fd39945dcec07ae44b` |
| dependency | `tail.md` | 192 | `dfb1a06e84060489a7f4535c75ec99141a86c9723526b0820d2e1551da245bbc` |

The two pressure files are each approximately 57.6 KB as required. The dependency workspace has explicit
`A.md → B.md → C.md → tail.md` references and unique root/tail identifiers. All filler is deterministic
ASCII generated from the stated seed; no credentials, private paths, or session content is embedded.

## 3. Frozen candidate prompts

### read-once-pressure

```text
Read exactly these files once each in this order with read_file: large-a.md, large-b.md, tail-1.md, tail-2.md, tail-3.md. Do not use search_files and do not re-read any file. After the fifth read, return only a JSON object with one key, tail_markers, whose value is an array of the exact TAIL_MARKER values in tail-1.md, tail-2.md, tail-3.md order. No commentary.
```

### deliberate-later-reread

```text
Read exactly these files once each in this order with read_file: large-a.md, large-b.md, tail-1.md, tail-2.md, tail-3.md. After all five reads, call read_file exactly one more time on large-a.md. Do not use search_files and do not re-read any other file. Then return only a JSON object with keys reread_ok (boolean true) and tail_markers (the exact TAIL_MARKER values in tail-1.md, tail-2.md, tail-3.md order). No commentary.
```

### dependency-chain

```text
Use read_file only. Read A.md, then follow its NEXT_FILE reference to B.md, then follow B.md's NEXT_FILE reference to C.md, then read tail.md once. Do not use search_files and do not re-read any file. Return only a JSON object with keys root_identifier (the exact ROOT_IDENTIFIER value from A.md) and tail_marker (the exact TAIL_MARKER value from tail.md). No commentary.
```

Prompt SHA-256 values:

- read-once-pressure: `8c8c7f7969d97f73349b2f667d1862d8eefa28c01036729860904fa077507ea3`
- deliberate-later-reread: `b9deee9837422de37738c00f610169d245429b9f41ab015b0da11bab79eec3bf`
- dependency-chain: `9d4e52bc8bbb1a377361a115744d0728b9eef3b2dbba193ba9c87179e7534466`

## 4. Expected mechanics and unverified outcomes

Using the plugin's `ceil(chars / 4)` page estimate:

- pressure fixture: `2 × 14,400 + 3 × 48 = 28,944` estimated page tokens before message overhead;
- dependency fixture: `14,400 + 14,400 + 7,200 + 48 = 36,048` estimated page tokens before message overhead;
- budget: `24,000`.

These totals establish only that the fixtures can exceed the budget. The live keep-law floor, exact
resident series, persisted drops, later `tool_recall`, and later `identifier_scan` remain **UNVERIFIED**
until authorized sessions run. No prompt or fixture broadening is permitted after ratification.

## 5. Research ratification checklist

Research/experiment must record all of the following before this becomes the freeze:

1. approve or amend the file set, byte sizes, hashes, seed, and exact prompts;
2. confirm the pressure shape still matches two ~57.6 KB files plus three tiny tails;
3. confirm the dependency shape preserves explicit A→B→C references and the intended later identifier;
4. publish a ratified manifest locator and its SHA-256 in the run record;
5. rerun `sha256sum -c`, collector `load_fixtures`, and a fresh live preflight;
6. only then authorize the bounded collector run under the existing owner ruling.

Any amendment requires a new draft version and new hashes. The collector must not consume this draft in
a live run before ratification.

## 6. Claim ceiling

No cost-saving, paging-quality, model-quality, determinism, availability, redaction, causal, or safety
claim. Candidate pins remain offline-only. `position_band`, `later_dependency_use`, and dependency
distance remain UNVERIFIED.
