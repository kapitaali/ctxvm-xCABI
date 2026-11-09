# OpenCode distribution — submission requirements vs adapter today (A4)

**Date:** 2026-11-09. Sources verified today: `https://opencode.ai/docs/plugins` (Configure/Discover/Control/Manage); `https://opencode.ai/docs/build/plugins` (Build); `https://opencode.ai/docs/ecosystem/` (docs-table list). Local adapter: `packages/opencode/live/ctxvm.ts`, `live/README.md`.

## How OpenCode distributes plugins (official docs)

- **Publish to npm** as a public package (GitHub-only repos are category 2 discoverable, but npm is the path). Checklist (docs "Plugins" §Manage + OpenDock submit page): `description`, `repository`, `license`, `README`, `keywords: ["opencode", "opencode-plugin"]`, plus the OpenCode installation example in the README.
- **Install via config** (`opencode.json(c)` `plugins` array: npm name with version/tag/range, scoped name, local dir, or Git spec `github:owner/repo`, incl. `::path:` subdirectory selector) or **CLI** (`opencode plugin add @scope/name@version`, `... list`, `... check`, `... update`, `... remove`).
- **Discovery**: direct `.ts`/`.js` files and immediate plugin package dirs under every `.opencode/plugins/` (project) or `~/.config/opencode/plugins/` (global). A root `plugins/` beside `opencode.json(c)` is *not* auto-discovered.
- **Marketplace list**: `https://opencode.ai/docs/ecosystem/` is a docs table (name + link + one-liner); "Want to add your project? Submit a PR" — one-row PR, reviewed.
- There is no separate "registry submission form"; the OpenDock page says: publish to npm with the keyword and you are listed the next day.

## What our adapter lacks today

| requirement | today | gap |
|---|---|---|
| npm public package | `private:true`, `0.0.1`, local shim only (`live/README.md`) | publish + rename: `@ctxvm/opencode` is 404 (verified 2026-11-09). Owner approval needed (D17) |
| `keywords` | absent from `package.json` | add `["opencode","opencode-plugin"]` |
| `files` allow-list | absent — dry-run ships 21 files incl. `test/` + `fixtures/*.jsonl` (see RR-PKG) | add `"files": ["dist","live","README.md"]` (or equivalent) + `LICENSE` |
| `LICENSE` in tarball | no `LICENSE` file in `packages/opencode/` (npm pack shows none) | copy root `LICENSE` into the package (pattern: `packages/node/LICENSE` + `cmp` gate) |
| `description`/`repository` | description present, repository absent in `packages/opencode/package.json` | add `repository.directory` like `@ctxvm/node` |
| README install example | `live/README.md` is the example, but tarball ships `src/` + `test/` instead of `dist/` | build to `dist`, point `exports`/entry at it; keep `live/README.md` as the published install steps (shim path must change from absolute repo path to installed package) |
| Version | `0.0.1` (pre-release) | publish `0.1.0` with the node adapter (lockstep) |
| Marketplace row | draft exists in `design/packaging.md` §5.2 (one-row docs-table PR) | owner approval, NOT submitted |

## Honesty notes

- The shim `export { default } from "/absolute/path/to/ctxvm/packages/opencode/live/ctxvm.ts"` is a *local-dev* path. In an installed package the import must be `@ctxvm/opencode` (or `@ctxvm/opencode/live`) — the published README must not carry the absolute path.
- The adapter is mirror-only (v0). The marketplace one-liner must say "read-only flight recorder" — no paging claim (law 7).

## Verdict

Mechanical gaps only (private flag, metadata, files, LICENSE, build). No hook-surface gaps: the live adapter works today via the shim. Effort: one card to fix metadata + build + README; submission itself is owner-gated.
