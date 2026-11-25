# RR-W22-LOCAL-NODE-20261125 — keep the DSH tracer dependency in ctxvm

Date: 2026-11-25. Scope: DSH stub packaging. Owner ruling: do not publish `@ctxvm/node` to npm; keep the package in the ctxvm repository.

## Change

- `ctxvm/packages/deepseek/package.json` now uses `"@ctxvm/node": "file:../node"`.
- `open-dsh/packages/deepseek/package.json` now uses `"@ctxvm/node": "file:../../../../Documents/ctxvm/packages/node"`.
- Both adapter READMEs describe the repository-local dependency and require a node-package build before adapter installation.
- `ctxvm/tools/ci-deepseek.sh` still builds and packs the tracer locally, but its comments and output now identify a repo-local tarball rather than an external registry package.
- The DSH stub-mode design and prior passive/active reports now record this packaging decision. Earlier publish/install instructions are marked superseded.

No runtime tracer or adapter behavior changed.

## Verification

A clean adapter install, after moving the existing `node_modules` aside, resolved the local dependency:

```text
added 1 package
installed @ctxvm/node 0.1.1
/home/theb/Documents/ctxvm/packages/node
```

Focused checks:

```text
@ctxvm/node: 30 passed, 0 failed
open-dsh adapter: 35 passed, 0 failed, 1 declared replay skip
open-dsh TypeScript: rc=0 with temporary workspace peer links; links removed
ctxvm ci-deepseek.sh: rc=0, 35 passing, 0 failed, 1 declared skip
checker: 13 passed
```

The passive and active local-mock stub runs had already passed against the same source: exact request stub bytes, one eviction/stub-render pair, valid sidecars, schema/checker success, and zero Rust replay divergences or violations.

## Status

The local dependency works from a clean install. No npm publish, registry lookup, push, gateway restart, or real-profile activation was performed.
