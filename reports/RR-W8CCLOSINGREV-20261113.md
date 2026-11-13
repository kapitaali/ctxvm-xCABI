# RR-W8CCLOSINGREV-20261113 — review of `RR-W8C-CLOSING-20261113` (`7ca4672`, plugin `0.13.19`): why `0.13.18` lost `evictedPagesCount` and `callSizes`, and why `0.13.19` still raises `UnboundLocalError` at `live/__init__.py:1465`

Card: review-lane audit of `3f0f7a0` (plugin `0.13.18`) and `7ca4672` (plugin `0.13.19`,
`reports/RR-W8C-CLOSING-20261113.md`).

---

## 1. The actual cause of the `0.13.18` failure — and it is **still present in `0.13.19` (`7ca4672`)**

`RR-W8C-CLOSING-20261113` states that `0.13.18` lost `evictedPagesCount` (`0`) and `callSizes` (`0`)
because *"re-attributing from the stamped policies was tried (0.13.18) and made it worse: the arm kept a
count of 41 while losing its own page detail."*

Reading `packages/hermes/live/__init__.py:1454–1486` at `3f0f7a0` (`0.13.18`) and `7ca4672` (`0.13.19`)
shows a different, mechanical cause — an **`UnboundLocalError` swallowed by `except Exception: pass`**:

```python
1454: def _record_selection(payload, _sid=_sid, _vm=_vm):
1455:     try:
1456:         _tr = _vm.tracer_for(_sid)
1457:         _tr.note_evicted(int(payload.get("evictedTokens") or 0))
...
1460:         _before = payload.get("beforeTokens")
1461:         _after = payload.get("afterTokens")
1462:         if isinstance(_before, int) and isinstance(_after, int):
1463:             _st = _state()
1464:             _st.setdefault("call_sizes_by_session", {}) \
1465:                 .setdefault(_target, []).append({"before": _before, "after": _after,
1466:                                           "dropped": payload.get("droppedCount")})
1467:             _st.setdefault("selections_by_session", {})[_target] = \
1468:                 _st.setdefault("selections_by_session", {}).get(_target, 0) + 1
1469:
1470:         _refs = _tr.refs_for_identity_tokens(payload.get("dropped"))
...
1480:         _target = _sid
1481:         if _refs:
1482:             _st = _state()
1483:             _st.setdefault("evicted_refs_by_session", {}) \
1484:                 .setdefault(_target, set()).update(_refs)
1485:     except Exception:  # noqa: BLE001 - observability must never break a turn
1486:         pass
```

### What happens on every selection call in **both** `0.13.18` and `0.13.19`:
1. Because `_target = ...` is assigned inside `def _record_selection` (at line 1480 in `0.13.19`, and at
   lines 1472/1475 in `0.13.18`), Python compiles `_target` as a local variable of `_record_selection`.
2. Line 1457 (`_tr.note_evicted(...)`) runs **before** line 1465, so `turn.render.evictedTokens`
   (`215,278`) succeeds.
3. Line **1465** references `_target` **15 lines before line 1480 assigns `_target = _sid`**, raising:
   ```
   UnboundLocalError: cannot access local variable '_target' where it is not associated with a value
   ```
4. Line **1485** (`except Exception: pass`) **silently swallows the `UnboundLocalError`** — the same
   bug class as `0.13.7` (`f1879a3`), where unimported `Path` and undefined `ENTERED` raised `NameError`
   inside `except Exception: pass`.
5. Because line 1465 aborts the `try` block:
   - `call_sizes_by_session` is never written (`callSizes: []`),
   - `selections_by_session` is never written (`{}`), and
   - lines 1470–1484 (`_refs = _tr.refs_for_identity_tokens(...)` and `evicted_refs_by_session`) are
     **never reached** (`evictedPages: []`, `evictedPagesCount: 0`).
6. And why did both sessions still show `41` selections in `.coverage.json`? Because `_coverage_manifest`
   (`packages/hermes/live/__init__.py:790`) sets `"engineSelections": _selections_total()`, which reads
   the module-global `ACTIVATIONS["select"]` (`41`), **not** `selections_by_session`.

### Reproducer (0 seconds, offline)

```bash
python3 - <<'PYEOF'
src = open('packages/hermes/live/__init__.py').read().splitlines()[1453:1486]
code_str = "\n".join(l[16:] for l in src).replace(
    "except Exception:  # noqa: BLE001 - observability must never break a turn\n        pass",
    "except Exception as e:\n        print(f'{type(e).__name__}: {e}')")
ns = {"_sid": "ses-1", "_vm": type("V", (), {"tracer_for": lambda self, s: type("T", (), {
    "note_evicted": lambda self, n: None, "refs_for_identity_tokens": lambda self, d: ["ref1"]})()})(),
    "_state": lambda: {}}
exec(code_str, ns)
ns["_record_selection"]({"evictedTokens": 100, "beforeTokens": 70000, "afterTokens": 59000, "dropped": [["part-01"]]})
PYEOF
# Output:
# UnboundLocalError: cannot access local variable '_target' where it is not associated with a value
```

---

## 2. Two additional inconsistencies in `7ca4672` (`0.13.19`)

1. **`engineSelectionsProcess` is in `_write_live_stamp` (`:405`), NOT in `_coverage_manifest` (`:790`)**:
   - `RR-W8C-CLOSING-20261113`’s table lists `engineSelectionsProcess` as a sidecar field, but
     `_coverage_manifest` (`packages/hermes/live/__init__.py:790`) was not updated and still writes
     `"engineSelections": _selections_total()`. Only `.live.json` (`_write_live_stamp`, `:405`) writes
     `"engineSelectionsProcess"`.
2. **`tools/w8-driver.py:352–358` still fails `"control selects nothing"` if a paged arm ran in the
   same gateway**:
   - `w8-driver.py:352` reads `_sel = plugin.get("engineSelectionsProcess") or plugin.get("engineSelections") or 0`
     and at `:358` asserts `_sel == 0` for `_control`. Because `_coverage_manifest` writes the
     process-wide `_selections_total()` into `"engineSelections"`, a control session flushed after a
     paged session in the same gateway still gets `_sel = 41` and fails `verify()`.

---

## 3. What stands in `RR-W8C-CLOSING-20261113` vs what needs a 3-line code fix in `packages/hermes/live/__init__.py`

- **What stands**:
  - The empirical results (**cell-02** free `0.60×` request; **cell-03** paid `$0.2534`, `0.57×` request,
    `2.11×` dollars, `72.2%` cache writes; **OpenCode vs Hermes** `13 vs 6` `turn.render` rows for `13 vs 12`
    requests; **no further paid spend**) are solid and unaffected.
  - Using `turn.render.evictedTokens > 0` in the trace as the primary per-session treatment proof is sound.
- **What `packages/hermes/live/__init__.py` needs so `0.13.19` matches the closing card's table**:
  1. Move `_target` resolution to **line 1455** (the top of `try:` inside `_record_selection`, **before**
     `_tr = _vm.tracer_for(_target)` and **before** line 1465), so `_record_selection` stops raising
     `UnboundLocalError` and `callSizes` / `evictedPages` / `evictedPagesCount` are populated again.
     (With `_pols = _state().get("policy_by_session") or {}` placed at line 1455, `0.13.18`'s
     paged-session target resolution also works cleanly because `_target` is bound before line 1465!)
  2. In `_coverage_manifest` (`:790`), emit `"engineSelectionsProcess": _selections_total()` and
     `"engineSelections": (_state().get("selections_by_session", {}) or {}).get(session_id, 0)` (or `0`
     when `arm == "control"`), and in `tools/w8-driver.py:352` read `plugin.get("engineSelections") or 0`
     for the per-session control check.
