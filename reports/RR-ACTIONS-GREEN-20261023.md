# RR-ACTIONS-GREEN — remote live + first Actions run green (2026-10-23)

**Outcome:** the repo is public at **https://github.com/kapitaali/ctxvm-xCABI**. The first
Actions run was rejected at workflow startup (latent `ci.yml` YAML bug from T10); after a
two-line fix, run **39942443159** is **GREEN on all four jobs** (`rust`, `ts`, `schema`,
`hub`) at commit `2b57cb1`.

## Timeline

1. **Push #1 (commit `cea293a`) — rejected by GitHub**: the fine-grained PAT lacked the
   **Workflows** permission, which GitHub requires for any push that introduces
   `.github/workflows/*`. Owner updated the token; no repo change needed.
2. **Push #2 — succeeded.** Run `39942284933` completed instantly with **0 jobs** — the
   signature of a workflow-level rejection. Diagnosis path: run API (`created_at ==
   updated_at`, `total_count: 0` jobs, 0 check-runs) → public run page payload →
   `Invalid workflow file: error in your yaml syntax on line 36`.
3. **Root cause:** line 36 was `- name: @ctxvm/node tests`. In YAML, `@` is a **reserved
   indicator** and cannot start a plain scalar — both `@`-prefixed step names were invalid
   YAML. The bug was latent since T10 because `ci.yml` had never executed anywhere (no
   remote); the local mirror (`tools/run-ci.sh`, bash) structurally cannot catch YAML
   syntax errors.
4. **Fix `2b57cb1`:** quoted both step names (`"@ctxvm/node tests"`,
   `"@ctxvm/opencode tests"`); pre-validated locally with PyYAML (venv) before pushing.
   Pushed.
5. **Run `39942443159` (head `2b57cb1`) — all four jobs completed/success**:
   `hub` · `ts` · `schema` · `rust` (~2 min wall).

## Verification (API, real outputs)

- `GET /repos/kapitaali/ctxvm-xCABI/actions/runs/39942443159` →
  `status: completed · conclusion: success · path: .github/workflows/ci.yml`
- `GET …/runs/39942443159/jobs` → `total_count: 4` — every job `completed / success`:
  `hub`, `ts`, `schema`, `rust`.
- Run URL: https://github.com/kapitaali/ctxvm-xCABI/actions/runs/39942443159
- Actions badge live in `README.md` (commit `cea293a`) — renders green from this run.

## What this validates beyond the mirror

- **T10's runner pins are now empirically exercised on `ubuntu-latest`** (previously
  "trusted mirrors of the local toolchain"): python 3.14 + `jsonschema==4.26.0` (schema job),
  node 26 (ts job), rust stable (rust job), `open-data-products==0.4.0` + hub regen
  byte-identity (hub job).
- The `hub` job's `git diff --exit-code hub/` check bites on a fresh checkout exactly as
  designed — regen reproduced the committed baseline byte-for-byte in CI.

## Notes / hygiene

- Reserved-indicator sweep (`^\\s*(- )?[A-Za-z_-]+:\\s*[@\\`]`): no other `@`/backtick-leading
  plain scalars remain in `ci.yml`.
- PATs were used inline for the pushes only — never written to `.git/config`, `.netrc`, or
  any file. Both tokens traveled through chat, so rotation after setup is advised.

## Open questions

- none.
