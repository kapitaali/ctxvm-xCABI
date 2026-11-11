# RR-LOGREWIND-20261111 — the working-tree LOG had been rewound by ten committed rows; restored
## before anyone could commit it away

Card: a kit-integrity finding of this lane's own. No experiment, no spend, no spec byte touched.

## 1. What was found

While reviewing the other lane's `3455f01` (plugin 0.11.0), this lane compared the **working-tree**
`reports/LOG.md` with the committed one (`git show HEAD:reports/LOG.md`) and found the working tree
was **behind the commit by ten rows**:

| | rows (non-empty lines) |
|---|---|
| `HEAD:reports/LOG.md` | 280 |
| working tree `reports/LOG.md` | 271 |

Ten committed rows were absent from the working tree — among them **this lane's** `RR-UHANDOFF-20261111`
and `RR-W8BCONTRAST-20261111`, and **the other lane's** `RR-W8B-ENGINE-20261111`, `RR-W8B-PAIR-20261111`,
`RR-W8B-PROMPT2-20261111`, `RR-W8B-PLUGINHOME-20261111`, `RR-W8B-CONTRAST-20261111`,
`RR-PLUGIN-ARMPOLICY-20261111` and `RR-W8B-PRUNEPROFILES-20261111`. A line-by-line subsequence check
(`reports/LOG.md` vs `HEAD:reports/LOG.md`) shows the working tree is a **strict subset** of the commit
in row order: the only working-tree line that is not byte-identical to a committed line is
`RR-HUBREF-20261111`, whose text was **reversed** in the working tree — the committed row states the
in-flight `hub/catalog.yaml` edit rewrites the reference from `"$ref: ../04-odps-dataproduct-corpus.yaml"`
to `"$ref: 04-odps-dataproduct-corpus.yaml"`, which is the direction `tools/build-hub.sh` step 3
restores (its `old = "$ref: 04-…"`, `new = "$ref: ../04-…"`), while the working-tree variant claims the
opposite. **The committed row is the correct one.**

## 2. Why this matters (the failure it would have caused)

`reports/LOG.md` is the append-only row ledger (law: never rewrite a committed row). Two things would
have happened on the next commit that staged the working-tree copy of the file:

1. **Ten committed rows would have disappeared from the record** — silently, because `git add
   reports/LOG.md` stages the *file*, not a diff against the previous commit, and the file was older
   than the commit. The other lane's rows would have been dropped from their own history at exactly
   the point where the record matters most (the measured defects: the CLI path never selecting, the
   plugin home, the no-contrast finding, the 0.11.0 arm policy).
2. **One committed row would have been rewritten** (`RR-HUBREF-20261111`), with the direction of the
   `$ref` change stated backwards — a factual rewrite of a committed row, which is the one thing the
   ledger's law forbids.

The rewound file's mtime (`2026-11-11 17:29:31`) coincides with the mtimes of this lane's day file
and roadmap, whose content is nevertheless identical to `HEAD` — so a bulk write touched the working
tree and left `reports/LOG.md` holding a **stale** copy. No stash exists (`git stash list` is empty) and
the reflog shows only ordinary commits, so the rewinding step itself leaves no trace in this repo's
history; the *effect* is what this card records.

## 3. What was done

- The working-tree copy was **restored to the committed one** (`git checkout HEAD -- reports/LOG.md`):
  ten rows added back, the reversed row restored to its committed text. Nothing of the working tree's
  own content was lost — the only worktree-only line was the corrupted variant of an existing row.
- Verified after the restore: the working tree and `HEAD:reports/LOG.md` are byte-identical, and the
  row count matches.

## 4. The standing rule this adds (for every lane that appends to the LOG)

1. **Append to the working tree AND commit a blob anchored at `HEAD`** — the two must agree. The recipe
   this lane uses: `git show HEAD:reports/LOG.md > f; cat row >> f; git update-index --cacheinfo
   100644,$(git hash-object -w f),reports/LOG.md`, committing through a temporary index
   (`GIT_INDEX_FILE`) so the shared index is never touched.
2. **After the commit, re-sync the working tree**: `git checkout HEAD -- reports/LOG.md`. A commit made
   from a temp index does **not** update the working tree, so a stale copy is the default state of that
   file — this is exactly how the ten rows went missing in the first place.
3. **Before staging the LOG, compare**: `diff <(git show HEAD:reports/LOG.md) reports/LOG.md` must show
   only *added* rows. If it shows deletions or a changed row, the working tree is stale — restore it
   before staging.
4. The kit check `bash tools/check-handoff.sh` does not cover this (it checks the kit's own files, not
   the LOG's freshness against `HEAD`), so the check above is manual and belongs to whoever stages.

## 5. Executed agent-doings

- The divergence was found while reviewing the other lane's commit; the ten missing rows and the
  reversed row were identified by a line-by-line subsequence comparison (not by eyeballing the diff);
  the direction of the `$ref` rewrite was checked against `tools/build-hub.sh` (its own `old`/`new`
  constants) rather than believed.
- The working tree was restored to the committed bytes; the standing rule was added.
- Kit: this card + LOG row + a day-file line. No other lane's file was edited; no spec, schema, corpus,
  vector or umpire byte changed; nothing pushed.
