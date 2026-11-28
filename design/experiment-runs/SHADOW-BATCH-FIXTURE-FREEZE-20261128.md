# SHADOW-BATCH-FIXTURE-FREEZE-20261128 — ratified inputs for the conditional shadow batch

Status: **FROZEN / RATIFIED FOR THE AUTHORIZED CONDITIONAL BATCH.**
Date: 2026-11-28
Ratified by: research/experiment, operator-confirmed 2026-11-28.
Authority: `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md`,
`reports/RR-SHADOW-COLLECTOR-FINAL-ACCEPTANCE-20261128.md`, and the ratified draft proposal
`design/experiment-runs/SHADOW-BATCH-FIXTURE-PROPOSAL-20261128.md`.

## 1. Frozen artifact

Private artifact name: `shadow-fixture-draft-20261128-v1` under the operator's ctxvm state directory.
The name is retained for byte identity; its status is now ratified, not draft.

- Manifest SHA-256: `202b9468ffa53301e7b56e29a2df92a3074c47ecb1a5f4164c50f820acdbc735`
- Generator SHA-256: `3c72e83e79e53374574df24889c32cef956874d4789cf17f517983663782f541`
- Generator seed: `20261128`
- Checksums: 12/12 pass
- Collector `load_fixtures`: all three shapes valid
- Private modes: directories 0700, files 0600

## 2. Frozen files

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

## 3. Frozen prompts

The exact prompts are the three strings in the ratified proposal and `manifest.json`. Their SHA-256
values are:

- read-once-pressure: `8c8c7f7969d97f73349b2f667d1862d8eefa28c01036729860904fa077507ea3`
- deliberate-later-reread: `b9deee9837422de37738c00f610169d245429b9f41ab015b0da11bab79eec3bf`
- dependency-chain: `9d4e52bc8bbb1a377361a115744d0728b9eef3b2dbba193ba9c87179e7534466`

No prompt or fixture broadening is allowed. Any change requires a new freeze, new hashes, and a new
authorization record.

## 4. Execution contract

- Model/provider: `tencent/hy4-flash:free` / `nous`; no paid fallback or silent switch.
- Anonymous one-shot attempts, `--max-turns 20`.
- Maximum 18 attempts, maximum six per shape.
- Stop at 12 new informative sessions: four per shape.
- Read-once requires a valid persisted drop; re-read adds later `tool_recall`; dependency adds later
  `identifier_scan`. Dependency distance remains UNVERIFIED.
- Any auth/model/provider-route failure stops collection immediately.
- Report all-valid and informative-only denominators; candidate pins remain offline-only.
- A fresh successful preflight is required immediately before execution.

## 5. Claim ceiling

No cost-saving, paging-quality, model-quality, determinism, availability, redaction, causal, or safety
claim. `position_band`, `later_dependency_use`, and dependency distance remain UNVERIFIED.
