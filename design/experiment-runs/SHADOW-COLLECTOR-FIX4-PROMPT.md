MASTER PROMPT — hermes/tools lane: final collector status/path/classification fixes

Authority: `reports/RR-SHADOW-COLLECTOR-ACCEPTANCE-REVIEW-20261128.md`. Three blockers remain. No live sessions
or gateway/profile/config changes.

1. **Status parser:** replace the non-greedy `dir/source/name` regex with unambiguous parsing. Embedded or
   duplicate ` (source: …), name=` text must fail closed, including paths introduced via `$VAR` expansion.
2. **Relative defaults:** reject non-absolute gateway trace paths or resolve them using proven gateway cwd.
   Collector cwd is not evidence of gateway cwd.
3. **Combined failures:** evaluate auth/model and route flags before branching. A route contradiction must remain
   `STOPPED_MODEL_PROVIDER` even when rc/auth failure is also present; write both reasons in the receipt.
4. Add no-model regressions for adversarial status text, relative XDG/default paths, and combined auth+route stops.
5. Rerun collector suite, full CI, rehearsal, kit, hygiene, diff, privacy. Append LOG02/day; private index; no push.

Live batch remains blocked until final acceptance.
