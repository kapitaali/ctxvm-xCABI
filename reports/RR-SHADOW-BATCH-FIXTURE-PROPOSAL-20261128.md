# RR-SHADOW-BATCH-FIXTURE-PROPOSAL-20261128 — draft freeze ready for research ratification

Hermes/tools drafting lane, operator-authorized proposal only. Date: 2026-11-28.
No live model call, session creation, gateway/profile/config change, restart, pin activation, publish, or push.

## 1. What was done

Created a deterministic private draft named `shadow-fixture-draft-20261128-v1` with three candidate
shapes, exact prompts, a `ctxvm-shadow-fixtures/v1` manifest, metadata, and checksums. The public proposal
is `design/experiment-runs/SHADOW-BATCH-FIXTURE-PROPOSAL-20261128.md`.

The draft is **not ratified** and is not authorized for live collection. Research/experiment owns the
freeze decision.

## 2. Candidate inputs

- Pressure workspace: two 57,600-byte files plus three 192-byte tail files.
- Dependency workspace: `A.md` 57,600 bytes, `B.md` 57,600 bytes, `C.md` 28,800 bytes, and a 192-byte tail.
- Generator seed: `20261128`.
- Manifest SHA-256: `202b9468ffa53301e7b56e29a2df92a3074c47ecb1a5f4164c50f820acdbc735`.
- Generator SHA-256: `3c72e83e79e53374574df24889c32cef956874d4789cf17f517983663782f541`.

The pressure prompts enforce sequential read-once behavior or one explicit later re-read of the first
large file. The dependency prompt follows explicit A→B→C references and asks for the root identifier in
the final answer.

## 3. Verification

```text
$ sha256sum -c checksums.sha256
12/12 entries OK

$ python3 tools/collect-shadow.py::load_fixtures(manifest.json)
all three shapes valid

root mode: 0700
workspace modes: 0700
all draft files: 0600
```

Estimated page-token totals using `ceil(chars / 4)`:

- pressure: `2 × 14,400 + 3 × 48 = 28,944`;
- dependency: `14,400 + 14,400 + 7,200 + 48 = 36,048`;
- budget: `24,000`.

These totals show only budget-scale pressure. Exact floor/resident behavior, persisted drops, later
`tool_recall`, and later `identifier_scan` remain UNVERIFIED until authorized live sessions.

## 4. Limitations and next action

- Research/experiment must approve or amend the files, hashes, seed, and exact prompts.
- Any amendment requires a new draft version and new hashes; no post-hoc broadening is allowed.
- After ratification, publish the freeze locator/SHA-256, rerun checksum and `load_fixtures` validation,
  and perform a fresh gateway preflight before the bounded batch.
- No metric, rate, candidate pin, causal, cost-saving, paging-quality, model-quality, determinism,
  availability, redaction, or safety claim is produced.

## 5. Repro commands

```bash
DRAFT_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/ctxvm/shadow-fixture-draft-20261128-v1"
(cd "$DRAFT_ROOT" && sha256sum -c checksums.sha256)
python3 "$DRAFT_ROOT/generate.py"  # deterministic regeneration; rewrites only the named draft root
python3 - <<'PY'
import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("collect_shadow_fixture_check", "tools/collect-shadow.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
print(sorted(module.load_fixtures(Path("REPLACE_WITH_DRAFT_ROOT") / "manifest.json")))
PY
```

The generator writes only inside the named draft root. It performs no network, model, gateway, profile,
or configuration access.

## 6. Applied

This report, the public design proposal, one four-pipe `reports/LOG02.md` row, one
`reports/RR-DAY-20261128.md` section, and a separate PROJECT-STATE delta. Private fixture bytes remain
outside git. No push.
