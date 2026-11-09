# Umpire positioning — demo vs library vs product (inputs only)

**Date:** 2026-11-09. **No choice made** — recommendation is an input to the owner.

## Options

### Option A — Demonstration of xCABI (lives under `examples/`)
Repo structure: move to `ctxvm/examples/umpire/` or keep as a consumer repo with a top-level badge. Maintenance: lowest (no npm/PyPI, no MCP stability promise). Evidence value for xCABI: high (fixtures prove the standard in use). Attention cost: low. A1–A5 impact: A1 stays "partial second implementation" (minting mirror), A5 finding stands, A3 packaging unchanged. Risk: if umpire evolves, the demo forks.

### Option B — Standalone product (`kapitaali/umpire`, own roadmap)
Repo structure: separate repo (current), PIP name must be qualified (`umpire` is taken on npm/crates/PyPI, A3). Maintenance: full product costs (hosted path, support, versioning). Evidence value: indirect (xCABI as consumer). Attention cost: high. A1–A5 impact: A1 remains a design erratum (second-impl phrase prohibited regardless), A4 MCP tools become the product surface, A5 invitation becomes marketing.

### Option C — Library extracted from umpire (`umpire` as a Python package: ledger + calibration math)
Repo structure: `packages/py` gains a ledger subpackage; harness/spawn tooling stays binary. Maintenance: medium (semver on the library, harness stays tool). Evidence value: high (the minting layer is the adoptable part — A1's 17/17 byte-identical minting is the library's proof). Attention cost: medium. A1–A5 impact: A1 becomes the library's conformance suite, A3 packaging covers it, A5's duplicate-ledger finding is the library's first page.

## Recommendation (input)

Option C: extract the ledger/minting library, keep the harness as an example. It is the only option where A1's evidence becomes a maintained artifact rather than a report. Option A is the fallback if the owner wants zero new maintenance.

What would change my mind: if D-U2 baselines beat calibrated umpire, Option B's product claim collapses to Option A regardless of structure.
