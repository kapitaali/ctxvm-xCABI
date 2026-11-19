# RR-RESVERIFY-20261119 — verified: Part III citation fixes, E1 offline landing, and the located datamining script

Review lane, verify-then-record. Subject: the three research-lane commits `e50d7b4` (`RR-DATAMININGFIX-20261117.md`),
`d10c325` (`RR-PART3FIX-20261119.md` + `research/white-paper-Part-III*.md`), and `a1bd004` (`RR-E1LAND-20261119.md` +
`research/e1-offline/**`). Date 2026-11-19. The research lane explicitly left `reports/LOG.md`,
`reports/RR-DAY-20261119.md`, and `handoff/PROJECT-STATE.md` to the review lane (`RR-PART3FIX` §4, `RR-E1LAND` §7).
This lane wrote no `research/**` byte, made no model call, no spend, and no push.

## 1. Part III citation fixes & the located datamining artifacts (`e50d7b4`, `d10c325`)

| check | command | result |
|---|---|---|
| positive citation grep (en / zh) | `grep -cE 'Zhong\|Souly' research/white-paper-Part-III.md` (and `.zh.md`) | `4` en, `4` zh |
| negative grep (en / zh) | `grep -cE 'Harding\|Chao et al\|2024-01-01\|descriptivepaired' …` | `0` en, `0` zh |
| file digests | `sha256sum research/white-paper-Part-III.md research/white-paper-Part-III.zh.md` | en `5ed93f729c9acd3d6f46ccb3129a8c24cb6dce6a148128aca808c676362f0f6f`; zh `deeb3f31e736b6fcc21e9e6746091aa872f102122a97bb9c33008ecc42c6500f` — exact match to card §2 |

**Correction to `RR-PART3FIX-20261119` §3 ("the exact THEMES/CTXVM_CONCEPTS regexes are lost"):**
They are **not lost on disk** — they are sitting in the gitignored directory
`research/uncommitted/materials/datamining/` (`.gitignore:40` ignores `research/uncommitted/`):

- `research/uncommitted/materials/datamining/datamining.py` (5,464 B, mtime 2026-11-17 19:18,
  sha256 `c34ea6bec7ea93169d35561101d3677570bfa14bb3eb4f849b8f055d1304c783`)
- `research/uncommitted/materials/datamining/datamining.json` (10,244 B, mtime 2026-11-18 10:00,
  sha256 `c533af6f86f89e451c28b0a8a61a75a6b26f3c9c88b69dbd3de6108837d23cd2`)

I ran `datamining.py` against `/home/theb/research/anthropic-papers-reference.sqlite` with `OUT` redirected to
`/tmp/opencode/datamining-repro.json`: it reproduces `datamining.json` **byte-for-byte** (`cmp -s` exit 0:
`n_papers: 1061`, `years: {2021: 148, 2022: 179, 2023: 232, 2024: 218, 2025: 137, 2026: 147}`,
`counterfactual` OR-aggregate `80`, `monitor_view` OR-aggregate `53`). Itremains true that those two files are
**not committed to git** (because they sit under `research/uncommitted/` rather than `research/datamining/`). Because
`research/**` is read-never-edit for the review lane, I did not move or stage them; the research lane can copy them
to `research/datamining/` if the owner wants them tracked in git.

## 2. E1 offline record & delegated data blockers (`a1bd004`, `RR-E1LAND-20261119`)

| check | command | result |
|---|---|---|
| manifest integrity | `(cd research/e1-offline && sha256sum -c manifest.sha256)` | **19/19 OK** (20 lines = 1 comment + 17 traces + `view-v1.py` + `PREREG.md`) |
| `view-v1.py` digest | `sha256sum research/e1-offline/view-v1.py` | `150d24cad23cf1b8ff16a066f109fd54bc3605a88e04424677fd098a558d5568` |
| privacy / corpus parity (law 9) | sha256 comparison of all 17 `research/e1-offline/traces/mNN__*` against `corpus/m*` via `path-map.json` | **17/17 byte-identical** to frozen public `corpus/m1`–`m8`; zero live/private traces committed |
| blocker 1 (15 paths / 13 names) | `research/e1-offline/path-map.json` + `PREREG.md` §1 | resolved by `mNN__<basename>` prefixing (no basename flattening; m2/m8 `live-echo`/`live-thrash` collision eliminated; 17 traces, 15 fault-bearing) |
| blocker 2 (live 247/4 vs 243/5) | `RR-E1LAND-20261119` §3 + `PREREG.md` §4 | resolved by retracting the non-reproducible live-dir snapshots and scoring only the frozen corpus; live `tool_recall` n=8 < 10 would trigger the prereg §4 stop rule (`tool_recall n < 10 -> Blocked`) regardless |
| replay reproduction | `(cd research/e1-offline && python3 replay1.py)` + `cmp -s` against landed `result.json` | reproduces `COUNTS {"A":{"identifier_scan":40,"tool_recall":12},"B":{"identifier_scan":41,"tool_recall":21},"control":{"identifier_scan":41,"tool_recall":21},"turns":96}`, `ADVANTAGE` 42.9% `tool_recall` (>10%, **label-quality signal only**) and 2.4% `identifier_scan` (≤10%, **negative result**), and writes a **byte-identical** `result.json` |

No answer, model-quality, paging, cost-saving (law 7) or unscoped determinism (law 8) claim is made; E2 remains
owner-gated.

## 3. Books closed by the review lane

- Appended the LOG rows owed for `RR-PART3FIX-20261119` / `RR-E1LAND-20261119` and this verification card
  (`RR-RESVERIFY-20261119`) to `reports/LOG.md` (four pipes each).
- Added the day-file section to `reports/RR-DAY-20261119.md`.
- Updated `handoff/PROJECT-STATE.md` to record Part III fixes and E1 offline replay as LANDED & VERIFIED.
