# RR-SUPPORT-20261030 — funding surface: README "Support this project" + the corpus-funding analysis

**Follows:** `README.md` (W11 honesty posture — the section is inserted after
Governance, leaving the measured-evidence blocks untouched) ·
`reports/RR-DECISIONS-20261030.md` (D5 $25 cap, D6 no-publish) ·
`reports/RR-DOGFOOD-20261029.md` (the evidence for why larger corpora are the
bottleneck)
**Card:** owner-directed 2026-10-30 ("add a support section; all donations used to buy
more compute and develop this project").
**Date:** 2026-10-30. Books + README only — no code, schema, corpus, package, or
publication change.

---

## 1. What was done

`README.md` gains a **"Support this project"** section (between Governance and Repo
map): the donation address, the donation policy, and the honest frame (no entity, no
tax deductibility, no perks — the only thing on offer is more measurement). Donations
raise the corpus budget above the current preregistered cap; the cap and its spend stay
recorded in `reports/`.

The address is copied verbatim from `~/Documents/bitcoin.txt` (owner's file, outside
the repo, never staged):

```
bc1qrdah46qfwkd03nqv88d9rw9mpgqat3ymhv0268
```

**Verified before publishing:** a bech32 (BIP-173) checksum validation was run on the
exact string — VALID bech32 witness v0, P2WSH (32-byte program), 42 chars. This catches
transcription corruption; nobody outside the owner can verify the address is theirs, so
the README re-verification hint is aimed at donors, not at us.

## 2. Why larger corpora are the bottleneck (grounded)

- All real captures to date are free-tier (nvidia NIM, opencode glm-5.3-flash-free;
  `prices.json` v1 records both as OBSERVED USD 0.00) — so **model spend is the
  binding constraint on corpus size**, not engineering.
- W1 (RR-DOGFOOD): no real session ever approached budget; zero evictions on real
  captures → W8 must create pressure deliberately, with a real paid model.
- W3: the re-anchored M0 gate (hard-fault recall ≥ 0.95, bootstrap 95% CI lower bound,
  n ≥ 30) is UNMEASURED at n = 4 hard faults — falsifiable in principle, "W8 supplies
  the volume".
- The owner's stated appetite: up to **$1,000** if funds materialize (2026-10-30),
  against the current D5 cap of $25.

| Budget | What it plausibly buys (directional, UNVERIFIED until W8 preregistration prices tasks) |
|---|---|
| $25 (current D5 cap) | the preregistered W8 pilot — directional read on ≥1.5x net-token reduction |
| ~$150–300 | one decisive W8 run with bootstrap CIs (n ≥ 30 turns per the M0 gate), baselines + treatment |
| ~$500–1,000 | policy sweep (several `FaultPinPolicy` variants), third-host live corpus, W5 cross-harness volume, and a hard-fault count that actually reaches the gate's n ≥ 30 |

## 3. Funding options considered (analysis, nothing applied)

| Option | Fit | Status |
|---|---|---|
| **Bitcoin donations** (now in README) | zero overhead; already live | **APPLIED** (owner-directed) |
| GitHub Sponsors / Liberapay / Ko-fi | cards + fiat rails; needs the owner's account setup | UNVERIFIED feasibility — owner account work, not attempted |
| **NLnet / NGI Zero grants** | funds small open-source internet/agent infra; typical grants in the €5k–50k class; individuals may apply | UNVERIFIED — specifics not re-checked 2026-10-30; **applying is an owner gate** (public exposure) |
| NVIDIA / cloud / lab researcher credits | the repo already runs on the NVIDIA NIM free tier (m8), so an existing relationship exists | UNVERIFIED — no application, no contact |
| **Paid harness-port work** (consulting) | the UC1/UC2 plugin work is portable; a client pays for a port, the corpus comes free | realistic near-term path; owner-time limited |
| Selling ODPS data products | the corpus is already packaged as ODPS 4.1 data products | **flagged with trade-offs, not recommended now** — conflicts with the open Apache-2.0 posture and D6's no-publish-until-W8; real-session consent questions; owner decides if ever |
| Anything token/scheme-shaped | — | **rejected** — incompatible with the measured-limitations posture |

## 4. Records

- Donation **usage** follows the existing books law: spend against donations is recorded
  in `reports/` when it happens (the W8 preregistration and its report will carry the
  actual billed spend per `RR-DECISIONS-20261030` rider 3).
- A dedicated public funding ledger (received/spent per hash) is a **v-next option** —
  useful for donor trust, but it publishes balance; owner decides.
- `~/Documents/bitcoin.txt` stays untracked; only the public address is in the repo.

## 5. Verification

- `README.md`: section inserted after Governance; no other section touched; the address
  in the README byte-equals the file's contents.
- Scans: CJK/`||`/NFC clean; LOG rows = 4 pipes; board rows = 6 pipes.
- Full `tools/run-ci.sh` ALL GATES GREEN before the commit; counts unchanged
  (`ts 13 + 58 + 45` / `python 83 + 44 + 8`).
- Reproduce: `python3 -` the BIP-173 check on the address (script inline in §1's
  description); `git show HEAD -- README.md`.
