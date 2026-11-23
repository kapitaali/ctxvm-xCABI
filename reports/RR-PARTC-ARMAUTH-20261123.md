# RR-PARTC-ARMAUTH-20261123 — owner authorizes one temporary experiment profile for the Part C stub arm

Owner decision 2026-11-23, verbatim (answer to the profile-choice question): **"Authorize one temporary experiment profile"** — the recommended option. This resolves the blocker for Part C condition 1 (opt-in stub arm, 8 sessions). Review lane, verify-then-record.

## 1. Why this was needed

The driver pins `HERMES_HOME` to `~/.hermes/profiles/{prefix}-{arm}`; the stub opt-in is a profile config setting
(`stubDropped`, env channel deliberately blocked by law). No existing profile carries it, and turning it on in the
shared `w8cn-paged` would make it default-on for real sessions (D6/D14 consent breach). Creating a profile is
normally forbidden (the owner's "never create profiles" rule after the 8-profile incident).

## 2. Authorization — bounded

- **Exactly one** temp profile (`w8cs-paged`) for the 8 stub-arm sessions; **no** change to any existing profile.
- Config: copy of `w8cn-paged` settings (`engine: ctxvm`, `budgetTokens: 24000`, model/provider) **plus**
  `stubDropped: recoverable`. Auth state (`.env`, `auth.json`, caches) **symlinked** from `w8cn-paged`, never copied —
  no credential duplication, no new secret material.
- Captures must attest `policyMode/stubDropped: recoverable` (source `settings`), proving the arm ran with the stub on.
- Cleanup: after the 8 sessions, delete **only** `~/.hermes/profiles/w8cs-paged` by exact path (law 10: never a
  variable that could be empty, never a parent), and verify the profile set is byte-for-byte the 10-profile baseline.
- Same frozen bank (`bank-36`), scorer, prompts, 8 sessions as Part B; re-read readout from trace `read_file` tool
  calls; no re-score/pooling of Part B. D17 held, no default-on change, no push.

## 3. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.
