# RR-W22PLANB-REVIEW — verified: Plan B landed, the proposed mechanism was replaced by measurement

Review lane, verify-then-record. Subject: `b701cc2` (ctxvm canonical), `5606cf1d` (DSH checkout),
`RR-W22-20261116-07.md`, and the recorded owner ruling "B is ok". No code change, no model call, no spend by
this lane. Plans C and D remain untouched.

## 1. Verdict

**Plan B is landed and verified.** The one-line peer declaration is present and byte-identical in both manifests;
all 16 adapter files remain identical; both hand-made `node_modules` link directories are empty, and both fresh
loads flushed named private traces with real identity. Importantly, the handoff's proposed mechanism was
**tested and rejected**, and the card says so rather than claiming the original plan succeeded. That is the
right record.

## 2. Evidence re-derived

| claim | command / source | result |
|---|---|---|
| landing | `git log`, `git show --stat b701cc2` | `b701cc2` present; one manifest line + card + LOG row; DSH HEAD `5606cf1d` |
| peer declaration | `grep -n -A6 peerDependencies packages/deepseek/package.json` | `@deepseek-ai/schemastery: "*"` alongside cordis and dsh-session |
| manifests identical | `diff -q` across trees | **IDENTICAL** |
| all adapter files identical | `find … -type f -not -path '*/node_modules/*'`, 16 files, `diff -q` | **16 compared, 0 mismatches** |
| hand-made links gone | `ls -l` both `node_modules/@deepseek-ai` dirs | both empty; no symlink |
| fresh loads | parse both named traces | both exist, `0600`, 5 events, `session.open` provider `opencode`, model `hy4-flash-free` |
| pnpm mechanism rejected | card §"proposed mechanism" | `pnpm install` rc=0 but no link; `pnpm --filter @ctxvm/dsh` matches no project; `workspace:~` trial produced no link and was reverted; lockfile/workspace files unchanged |
| suite | `node --test packages/deepseek/test/` | **15 / 14 pass / 0 fail / 1 named skip** |
| gate | my own re-run during this review | rc=0 **ALL GATES GREEN** (2026-11-17, `/tmp/opencode/20261117-planb-ci.log`, ambient `CTXVM_*` cleared) |

## 3. What changed in the record

The handoff's UNVERIFIED claim — "`*` peer plus `pnpm install` generates the vendored link" — is **FAILED as a
mechanism**, but the change itself works by a different route: the DSH host resolves the declared peer directly.
Two consequences to carry forward:

- Do not re-attempt the `pnpm install` / `workspace:~` path on the strength of the original handoff. It is tested
  and rejected in `RR-W22-20261116-07`.
- `packages/deepseek` is not a pnpm workspace importer (`pnpm-workspace.yaml` uses `packages/*/*`). Any future
  dependency fix that assumes workspace resolution must first check this.

## 4. Still not authorized / not done

Plan C (acceptance #4): still held on the credential and the failed-turn 400 route decision. Plan D: the two
always-false ternaries in another lane's `import-hermes-credentials.ts` remain that file's owner's work. No
push, no cost or model-output claim. Trace bytes and credentials stay private. The literal `~/` artifact in the
DSH checkout is still reported and untouched; no recursive delete at a home-resolving path.

Kit/gate: `check-handoff.sh` ALL PASS; `git-hygiene.sh` OK. This card changes no gate input.
