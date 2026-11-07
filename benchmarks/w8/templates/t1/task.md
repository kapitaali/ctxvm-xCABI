# Task T1 — the CLI reference table for this project

This workspace holds a source snapshot of the `ctxvm` project — the repository's own code,
which you are documenting for its README. The snapshot is in this workspace. Its sources are split into line-aligned parts so that no single read is large:
`MANIFEST.tsv` maps every `*.partNN` file back to its logical path (`logical_path`), its
line range, and a digest. Concatenating a file's parts in manifest order reproduces the
source exactly.

Write the audit as **`flags.json` in the workspace root**. Nothing else is part of the
answer.

## Deliverable schema

```json
{
  "binaries": [
    {"binary": "replay.rs", "flags": ["--help", "--turn"], "coreFunction": "cli::replay_core"}
  ],
  "lineShape": [
    {"file": "rust/crates/ctxvm-core/src/render.rs", "lines": 812, "maxLineBytes": 118, "overlong100": 4}
  ],
  "publicSurface": [
    {"file": "rust/crates/ctxvm-core/src/render.rs", "items": [{"kind": "fn", "name": "derive_projection"}]}
  ]
}
```

* `binaries` has one entry per CLI binary in `MANIFEST.tsv`, in the order the binaries first
  appear there. `binary` is the file name only (`replay.rs`, not the full path).
* `publicSurface` has one entry per logical file, in `MANIFEST.tsv` order, using the logical
  path. A file with no public items gets `"items": []`.

## Rules — these are the whole specification

1. **Accepted flags.** A long flag (`--name`) counts as accepted by a binary only when its
   literal appears as a match pattern in that binary's own argument loop — the `"--turn" =>`
   arms of the loop that walks `args`/`argv`. Patterns in doc comments (`//!`, `///`), in
   `USAGE` constants, and in `help()` bodies are prose, not parser behaviour, and are not
   authoritative. List a binary's flags in the source order of each flag's first pattern.
   Record the long form only; a short alias (`-h`) in the same arm is not listed.
2. **Core function.** `coreFunction` is the first `cli::<name>(` call inside the binary's
   `main()` — the conformance-library function the binary hands its parsed arguments to,
   written as `"cli::<name>"`. If `main()` makes no such call, the value is `null`.
3. **Line shape.** For each file, `lineShape` records:

   * `lines` — how many lines the file has; a trailing newline does not open a line. The
     manifest's `lines` ranges describe the parts, and summing them is a legitimate check,
     but the file's own bytes are the answer.
   * `maxLineBytes` — the byte length of the file's longest line, newline excluded, measured
     in **UTF-8 bytes, not characters**: a typographic dash (`—`) is three bytes, `…` is
     three, an accented letter two. This is not derivable from the manifest or from any
     match list — it must be measured over every line of the file.
   * `overlong100` — how many lines are longer than 100 bytes, same encoding rule.

   A search returns the lines that match a pattern; it never reports the shape of the file.
4. **Public items.** For each file, `items` lists every declaration whose line begins at
   column 0 with `pub ` and is one of `pub fn`, `pub struct`, `pub enum`, `pub trait`,
   `pub const`, `pub type`, `pub mod`. Record `kind` (the keyword) and `name`. Exclude
   `pub(crate)` and anything indented (methods inside `impl` blocks are not top-level
   items). Keep source order.

Read the parts you need; do not guess. When you are done, `flags.json` must be the only file
you created.
