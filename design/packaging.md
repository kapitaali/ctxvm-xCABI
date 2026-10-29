# Packaging and distribution — preparation (W10)

**Status: PREPARE ONLY. Nothing here is published, submitted, or tagged.**
Every publish/submit/tag action is behind the owner gates in
`08.1-UPDATE-PROMPT.md` §3 (human approval). This document records what is ready,
what is **not** ready, and the exact blockers found on 2026-10-29. It is the W10
artifact; the report is `reports/RR-W10-20261029.md`.

**Card:** W10 — "Packaging and distribution (prepare; publish only with approval)".
**Scope actually executed:** lane-free preparation. No file under
`packages/node/` or `packages/hermes/` was edited (standing do-not-touch lanes);
package metadata changes are recorded here as **proposals**, not applied.

---

## 1. Package inventory and readiness

| Registry | Package | Version | State | Blocker before publish |
|---|---|---|---|---|
| npm | `@ctxvm/node` | 0.1.0 | source-only TS package | **hard blocker:** `exports` points at `./src/index.ts`; Node refuses TypeScript under `node_modules` (locator §6.2). Needs a JS build + `.d.ts` + `files` allow-list + LICENSE. |
| crates.io | `ctxvm-core` | 0.1.0 | packages, does not publish | **hard blocker:** path dependency `ctxvm-codec` has no version requirement (dry-run exit 101, §6.3). |
| crates.io | `ctxvm-codec` | 0.1.0 | publishable today | warnings only: no repository/homepage/documentation; crate tarball carries no LICENSE/README. |
| crates.io | `ctxvm-tokenizer` | 0.1.0 | not dry-run | depends on workspace path deps (same class as `ctxvm-core`). |
| crates.io | `ctxvm-conformance` | 0.1.0 | not dry-run | depends on three workspace path deps; also ships the CLI binaries (its reason to exist). |
| PyPI | `ctxvm-py` | 0.1.0 | wheel builds | **hard blocker:** wheel is a subprocess wrapper around Rust binaries; on a clean machine there is nothing to call. Needs bundled platform wheels or a documented/auto-installed `cargo install` dependency. |
| Hermes index | `ctxvm-tracer` | 0.2.0 | installable from Git today | entry is drafted (§5.1); submission is gated. |
| OpenCode ecosystem | `ctxvm` adapter | 0.0.1 | installable as a local plugin today | entry is drafted (§5.2); submission is gated. |
| npm | `@ctxvm/opencode`, `@ctxvm/ai-sdk` | 0.0.1 | **`private: true`** | These are harness integrations, not published libraries in v0. The OpenCode route today is the local plugin file. |

There is **no single `ctxvm` dispatcher binary**; the CLIs are five separate
binaries: `replay`, `profile`, `diff`, `export`, `tokens` (crate
`ctxvm-conformance`). Docs and quickstarts must not promise `ctxvm profile` until
such a binary exists.

There are **no git tags** in the repository (`git tag -l` is empty). Tag creation
is deferred to the approved release; the plan is in §7.

## 2. Name availability (checked 2026-10-29T19:39:56Z)

HTTP status from the public registries: `404` = no such package/mark in that
namespace at check time; `200` = exists (detail fetched for collisions).

| Name | npm | crates.io | PyPI | GitHub user/org |
|---|---|---|---|---|
| `ctxvm` | **404 (free)** | **404 (free)** | **404 (free)** | user 404, org 404 |
| `xcabi` | **404 (free)** | **404 (free)** | **404 (free)** | user 404, org 404 |
| `umpire` | **200 — taken** | **200 — taken** | **200 — taken** | org 200 (2013, 0 public repos) |
| `ctxvm-core` | — | **404 (free)** | — | — |
| `ctxvm-codec` | — | **404 (free)** | — | — |
| `ctxvm-tokenizer` | — | **404 (free)** | — | — |
| `ctxvm-conformance` | — | **404 (free)** | — | — |
| `ctxvm-py` | — | — | **404 (free)** | — |
| `@ctxvm/node` | **404 (no package)**; scope ownership UNVERIFIED | — | — | — |

Collision details for `umpire` (all unrelated to this project):

- npm `umpire@0.0.1` — "A logical framework", repo `ben-ng/umpire`.
- crates.io `umpire@0.4.0` — "Combat Quest of the Millennium", repo
  `joshhansen/Umpire`, 1,969 downloads.
- PyPI `Umpire@0.8.2` — "Generic dependency resolver", Signiant.
- GitHub org `umpire` — created 2013-11-24, 0 public repos.

**Consequence:** the bare `umpire` name is unavailable on every public package
registry and as a GitHub org. The repository can keep its local name, but any
future publication must use a qualified name (for example a `@kapitaali/umpire`
npm scope or a distinct PyPI/crates name) and must not claim the bare name.

**Scope caveat:** npm scope availability (`@ctxvm`) is not publicly queryable;
`https://www.npmjs.com/org/ctxvm` returned HTTP 403 (not interpretable). The
scope is claimed on first publish by the owning account. Treat scope ownership as
**UNVERIFIED** until the owner checks `npm org ls` while logged in. GitHub user
and org names `ctxvm`/`xcabi` are free as of the check.

## 3. Trademark check (NOT a clearance search)

A targeted web search on 2026-10-29 for the exact marks (`"CTXVM" trademark
software`, `"xCABI" agent trace standard`) surfaced **no record for either mark**.
That is a search-result observation only, **not legal clearance**: no USPTO,
EUIPO, or WIPO register was queried, and no similarity search was run. Trademark
status is **UNVERIFIED**. Before publishing, commission a proper clearance search
(or at minimum query USPTO TESS/EUIPO eSearch) for `ctxvm`, `xCABI`, and any
qualified `umpire` name.

Related naming risk (not a trademark): **"Agent Trace" is an existing draft
standard** — Cursor's attribution format, RFC 0.1.0, January 2026
(`https://agent-trace.dev/`, announced at
`https://www.infoq.com/news/2026/02/agent-trace-cursor`). It records AI code
attribution (file/line provenance), not pages/faults/replay, so the formats do
not collide technically. The *words* are close enough that xCABI should keep its
own name and state the distinction in any launch text: xCABI is a context
page/fault/replay trace, not a code-attribution record. `ctxvm` and `xCABI` are
explicitly working names (`README.md`, top).

## 4. Dependency-license audit (Apache-2.0 compatibility)

Method: `cargo metadata --format-version 1` (default and `--features tiktoken`),
npm registry metadata for dev dependencies, and import scans of the Python
packages. Results, 2026-10-29:

### 4.1 Rust (resolved graphs, workspace + transitive)

| License expression | Packages | Verdict |
|---|---|---|
| `Apache-2.0` | the four workspace crates | own code |
| `MIT OR Apache-2.0` | `itoa`, `proc-macro2`, `quote`, `serde`, `serde_core`, `serde_derive`, `serde_json`, `syn` | compatible |
| `MIT` | `zmij` (default); `fancy-regex`, `tiktoken-rs` (feature) | compatible |
| `Unlicense OR MIT` | `memchr`; `aho-corasick` (feature) | compatible |
| `(MIT OR Apache-2.0) AND Unicode-3.0` | `unicode-ident` | compatible (Unicode-3.0 is permissive) |
| `Apache-2.0 OR MIT` | `bit-set`, `bit-vec`, `rustc-hash` (feature) | compatible |
| `MIT OR Apache-2.0` | `anyhow`, `base64`, `bstr`, `regex`, `regex-automata`, `regex-syntax` (feature) | compatible |

No GPL, LGPL, AGPL, SSPL, or other copyleft license appears in either graph.
**Obligations before publish:** preserve the copyright/license notices of the
MIT/Unlicense/Apache-2.0 dependencies and ship an Apache-2.0 `LICENSE` with each
package. No `THIRD-PARTY-NOTICES` file exists yet; generating one is a
publish-time task, not done here.

### 4.2 Node / TypeScript

- `@ctxvm/node`: **zero runtime dependencies**; `license: Apache-2.0`.
- `@ctxvm/ai-sdk`: private; dev-only `ai@7.0.154` and
  `@ai-sdk/openai-compatible@^3.0.79`, both **Apache-2.0** (registry latest at
  check: 7.0.157 / 3.0.81; the pin is what matters and it is Apache-2.0).
- `@ctxvm/opencode`, `@ctxvm/hermes`: no runtime dependencies listed.

### 4.3 Python

- `ctxvm-py`: standard-library imports only (`json`, `os`, `subprocess`,
  `pathlib`, `typing`, ...). It shells out to the Rust binaries.
- Hermes plugin + benchmarks: standard library plus local modules; `pytest` is
  dev-only (MIT).
- Gate-only (not distributed): `jsonschema` (MIT), the ODPS SDK
  `open-data-products==0.4.0`. The SDK's PyPI metadata declares **no license
  field** and its repository reports `NOASSERTION`/Other — **UNVERIFIED**. It is
  used only by the hub CI job and is not bundled into any package.

**Verdict:** the dependency graph is Apache-2.0-compatible; no copyleft. The
remaining license tasks are notice-file generation and LICENSE inclusion in
package tarballs/wheels, both gated on the publish decision.

## 5. Draft index entries (prepared, NOT submitted)

### 5.1 Hermes plugin catalog

Locator: the official catalog docs
(`https://hermes-agent.nousresearch.com/docs/user-guide/features/plugin-catalog`)
state the index is a plain JSON file in `NousResearch/hermes-plugin-index`, with
entries carrying name, description, author, tags, `owner/repo`, and a pinned
commit SHA; submission is a pull request. The documented canonical index URL
(`https://raw.githubusercontent.com/NousResearch/hermes-plugin-index/main/index.json`)
returned HTTP 404 at check time, so the **exact JSON key names are UNVERIFIED**;
the draft below uses the documented field names.

```json
{
  "name": "ctxvm-tracer",
  "title": "ctxvm tracer",
  "description": "Read-only xCABI flight recorder: deterministic JSONL traces of pages, faults and renders for replay and context accounting.",
  "author": "kapitaali",
  "category": "tools",
  "tags": ["observability", "telemetry", "tracing", "xcabi"],
  "owner": "kapitaali",
  "repo": "ctxvm-xCABI",
  "subdir": "packages/hermes",
  "ref": "<pin the release commit SHA>",
  "version": "0.2.0",
  "docs_url": "https://github.com/kapitaali/ctxvm-xCABI/blob/main/packages/hermes/HOOKS.md"
}
```

Notes: catalog review is **metadata-only**, not a code audit (same docs). The
plugin is installable from Git today (`hermes plugins install kapitaali/ctxvm-xCABI`
with `subdir`, subject to Hermes' own resolver) or by copying
`packages/hermes/live/`. Do **not** submit before the owner approves publication.

### 5.2 OpenCode ecosystem

Locator: `https://opencode.ai/docs/ecosystem/` — the plugin list is a docs table
of name + link + one-line description, and the page says "Want to add your
OpenCode related project to this list? Submit a PR." Draft row (not submitted):

```md
| [ctxvm](https://github.com/kapitaali/ctxvm-xCABI/tree/main/packages/opencode) | Read-only xCABI flight recorder: deterministic page/fault/render traces you can replay and profile |
```

Install path today is the local plugin shim (`.opencode/plugins/ctxvm.ts`,
`packages/opencode/live/README.md`), because publishing the adapter to npm is
blocked by the same TypeScript-in-`node_modules` issue (§6.2). A future npm
package is the natural post-build route; the ecosystem list itself accepts a
repository link.

### 5.3 Claude Code hooks

The card says "after W5". W5 has not run, so this was **not checked** and is
deferred by design.

## 6. Publish blockers found (evidence)

### 6.1 Reproducible install commands (README quickstart)

Verified against the checkout: `cargo build --release` then
`./rust/target/release/profile corpus/m5/opencode-live-session-01.jsonl` and
`replay` on the same trace (exit 0). `cargo install --path
rust/crates/ctxvm-conformance` installs the five binaries. No registry install
exists yet.

### 6.2 npm: TypeScript source cannot ship as an installed dependency

`npm pack --dry-run` (packages/node) reports 10 files, 11,621 B tarball /
38,649 B unpacked, **no LICENSE**, and includes `test/` and `fixtures/`. The
package's `exports` maps `"."` to `./src/index.ts`. The Node.js TypeScript docs
state: "Node.js refuses to handle TypeScript files inside folders under a
`node_modules` path" (`https://nodejs.org/api/typescript.html`, "Type stripping
in dependencies"). Therefore an npm install of the current package cannot load
it, regardless of Node version.

Secondary finding: even for local execution, type stripping is **enabled by
default** from Node v22.18.0 / v23.6.0 (same page, history table), while
`engines` says `>=22.6.0` — the floor that introduced the experimental flag.
The published package must be built to JS; the engines field should be raised or
the build target documented.

Proposed metadata changes (NOT applied): add a build step and `files`
allow-list, ship `LICENSE`, add `repository`, and point `exports` at built output.

### 6.3 crates.io: path dependencies without versions

```
$ cargo publish --dry-run --allow-dirty -p ctxvm-core
error: failed to verify manifest .../ctxvm-core/Cargo.toml
Caused by: all dependencies must have a version requirement specified when publishing.
  dependency `ctxvm-codec` does not specify a version
EXIT=101
```

`ctxvm-codec` alone:

```
$ cargo publish --dry-run --allow-dirty -p ctxvm-codec
warning: manifest has no documentation, homepage or repository
Packaged 7 files, 22.9KiB (7.7KiB compressed)
Finished ... (verification build)
EXIT=0
```

Proposed fix (NOT applied): add `version = "0.1.0"` alongside `path` in
`[workspace.dependencies]`, add `repository`/`readme` to the workspace package
metadata, and include the root `LICENSE` in each crate (via `license-file` or
`include`). Crate names are free (§2).

### 6.4 PyPI: the wheel needs the Rust binaries

`python3 -m pip wheel --no-deps packages/py` builds
`ctxvm_py-0.1.0-py3-none-any.whl` (4,939 B). It contains the three Python
modules and metadata only; `_cli.py` resolves `replay`/`profile`/... from
`CTXVM_RUST_BIN_DIR`, a repo-relative `rust/target/release`, or `PATH`. A user
who installs only the wheel gets `RuntimeError: ctxvm <name> binary not found`.
Publishing as-is would be a broken install. Options (owner decision): publish
platform wheels that bundle the binaries, or declare+document the Rust build as
a prerequisite (for example a console entry that runs `cargo install`), or keep
the binding repo-only until the PyO3 binding lands.

## 7. Versioning and tag plan (deferred)

- Workspace/package versions today: `0.1.0` (rust crates, `@ctxvm/node`,
  `ctxvm-py`); harness integrations are `0.0.1` and private.
- The schema is **v0 and sealed** (`spec/rfc-0/`); it is versioned by the schema
  file and RFC, not by package semver. RFC-0.1 is a W7 proposal awaiting D4.
- Proposed release sequence, only after approval: (1) build artifacts and
  notice files; (2) tag the exact release commit (`v0.1.0`); (3) publish
  crates/npm/PyPI from that tag; (4) then submit index entries pinned to the tag
  commit. No tags exist or are created by this card.

## 8. Explicitly not done

- No package, crate, wheel, or release was published.
- No index entry was submitted; no PR was opened.
- No git tag was created or pushed.
- No schema or RFC file was touched.
- No `packages/node/` or `packages/hermes/` metadata was edited (lane rule);
  §6.2/§6.3 proposals need owner clearance.
- No hub/llms.txt/manifest edits (W11 scope rule: W10 owns packaging, but the
  hub itself stays frozen until an outside trace exists).
