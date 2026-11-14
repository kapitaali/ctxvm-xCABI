# RR-CHECKER-GAPS-20261114 — the ruled per-call rule is half live: the fail-closed half is **not** enforced for a capture with **no per-call list at all**, and the shape rule's precondition is **never written** by the adapter (five variants, zero spend)

Card: review-lane check of the checker's per-call rule (the hermes lane's `f3078b4` ✓, `tools/coverage_check.py` ✓)
against the **P12 ruling** ✓ (recorded in `reports/RR-OMISSIONANSWER-20261113.md` ✓): *"a capture with removals
and no list is a violation"* ✓. **Two holes**, both reproduced on synthetic sidecars derived from the real
0.13.21 capture ✓ — **no spend** ✓, no capture, no code change ✓.

---

## 0. Verdict

The rule that shipped ✓ does enforce two of the ruling's three clauses ✓ and **not** the third ✓:

| the ruling's clause ✓ | implemented? ✓ | evidence ✓ |
|---|---|---|
| a dropping call must **name** what it removed ✓ | **YES** ✓ | variant **b** ✓ ⇒ 16 violations ✓ |
| the named tokens must account for the size change ✓ | **YES** ✓ (10 % tolerance ✓) | variants **f**/**g** ✓ |
| **a capture with removals and no list is a violation** ✓ | **NO** ✓ | variants **c** and **e** ⇒ **consistent, exit 0** ✓ |

⇒ ⇒ **one ask for the adapter** ✓ (write `plugin.evictedTokens` ✓) ⇒ **one ask for the checker** ✓ (require
the **per-call** list, not the union count ✓) ✓ ⇒ ⇒ both are one-liners ✓ ✓.

---

## 1. The repro (five variants, derived from the real 0.13.21 capture ✓)

```
python3 - <<'EOF'
import json, glob, os, hashlib, subprocess
cov = sorted(glob.glob(os.path.expanduser(
    '~/.local/state/ctxvm/traces/local-d60a50c44acf*.coverage.json')))[0]
tr  = cov.replace('.coverage.json', '.jsonl')
base = json.load(open(cov))
digest = hashlib.sha256(open(tr, 'rb').read()).hexdigest()
def write(name, mutate):
    d = json.loads(json.dumps(base)); mutate(d)
    d['traceDigest'] = digest; d['traceFile'] = 'trace.jsonl'
    p = f'/tmp/{name}.coverage.json'; json.dump(d, open(p, 'w'))
    r = subprocess.run(['python3', 'tools/coverage_check.py', tr, p],
                       capture_output=True, text=True)
    print(name, 'exit', r.returncode)
EOF
```

⇒ the outcomes ✓ (each variant differs from the real sidecar only as named ✓):

| variant ✓ | what it changes ✓ | result ✓ |
|---|---|---|
| **a** ✓ | none (the real 0.13.21 capture ✓) | **consistent** ✓ — exit 0 ✓ ⇒ the per-call rule is **version-gated off** below 0.13.23 ✓ ✓ |
| **b** ✓ | version → 0.13.23 ✓; every dropping call gets `removed: []` ✓ | **violations** ✓ — exit 1 ✓, one per dropping call ✓ (*"call 0: 4411 tokens left the request but no removed pages are named"* ✓) ⇒ ⇒ **the fail-closed direction is live** ✓ ✓ |
| **c** ✓ | version → 0.13.23 ✓; **`callSizes` emptied** ✓ (the removals happened; there is **no list**) | **consistent** ✓ — exit 0 ✓ ⇒ ⇒ **the hole** ✓ ✓ |
| **d** ✓ | version → 0.13.23 ✓; `evictedTokens = 5000` ✓; `evictedPagesCount = 0` ✓; `callSizes` emptied ✓ | **violation** ✓ — exit 1 ✓ (*"evictedTokens > 0 but no per-page detail"* ✓) ⇒ ⇒ the **shape rule** fires **when the key is present** ✓ ✓ |
| **e** ✓ | as **d** ✓ but `evictedPagesCount = 9` ✓ (the union is there ✓) and `callSizes` emptied ✓ | **consistent** ✓ — exit 0 ✓ ⇒ ⇒ **the union count satisfies the shape rule even with no per-call list** ✓ ⇒ ⇒ the hole survives ✓ ✓ |

⇒ **the two consistency clauses** ✓ (the ruling's second clause ✓): variant **f** ✓ (the named tokens off by
**50 %** ⇒ *"removed pages name 2205 tokens against an actual drop of 4411 (tolerance 10 %)"* ⇒ exit 1 ✓) and
variant **g** ✓ (off by **5 %** ⇒ exit 0 ✓) ⇒ ⇒ the tolerance is live and stated ✓ ✓.

---

## 2. The two asks, each one line

### 2.1 The adapter must write the session's removal total into the sidecar ✓

The sidecar's `plugin` block (0.13.23 ✓) carries ✓: `version`, `harness`, `harnessVersion`, `engine`,
`engineSelections`, `engineSelectionsProcess`, `profile`, `arm`, `engineSetting`, `skippedControl`,
`budgetTokens`, `budgetSource`, `evictedPages`, `evictedPagesCount`, `engineEntered`, `callSizes` ✓ — and
**`evictedTokens` is not among them** ✓ ⇒ ⇒ the shape rule's precondition
(`plugin.evictedTokens > 0` ✓) is **never satisfied** ✓ ⇒ ⇒ the rule is **dormant in production** ✓ ✓ (the
finding of `reports/RR-VERSIONDRIFT-20261113.md` ✓ and `reports/RR-INSTRUMENT023-20261113.md` §2 ✓, now
with a repro ✓ and for 0.13.23 ✓ ✓).

⇒ The number already exists ✓: the plugin keeps it per turn ✓ (`packages/hermes/src/plugin.py:564` ✓:
`"evictedTokens": self._evicted_by_turn.get(t, 0)` ✓) ⇒ ⇒ a session sum is one line ✓ ✓.

### 2.2 The checker must require the **per-call** list, not the union count ✓

Variant **e** ✓ shows the gap ✓: with `evictedTokens > 0` ✓ and the union count present ✓, a capture with
**no per-call list** passes ✓ ⇒ ⇒ the ruling's clause *"a capture with removals and no list is a violation"* ✓
is unenforced ✓ ⇒ ⇒ the rule needs a third clause ✓: *if the session removed tokens ✓, some per-call entry must
carry a non-empty `removed` list ✓* ✓ ⇒ ⇒ which is exactly the shape the ruling described ✓ ✓.

⇒ ⇒ with 2.1 ✓ and 2.2 ✓ together ✓, the three clauses of the ruling ✓ are all enforced ✓ ⇒ ⇒ and the
**first live witness** becomes possible ✓ ⇒ ⇒ the next capture on **0.13.23** ✓ (the gateway drift has closed ✓
⇒ any new gateway loads 0.13.23 ✓) would exercise it ✓ ⇒ ⇒ ⇒ **that is the capture to take** ✓ ✓.

---

## 3. What this does **not** change ✓

- The ruling ✓ (wire ✓, per call ✓, fail closed ✓, addition ✓, sidecar as fallback ✓) ✓ — unchanged ✓ ✓.
- The capture-side instrument ✓ (per-call identities with token counts ✓, delivered in `f3078b4` ✓) ✓ —
  unchanged ✓ ✓ (the instrument **is** there ✓; the checker's reading of it is what has the holes ✓ ✓).
- The **preregistered** W8D conclusion ✓ (the refusal ✓) ✓ — unchanged ✓ ✓.
- The **scope** of the rule ✓: it is a **sidecar-consistency** check ✓, not a proof about the request ✓ ⇒
  the provider's receipts remain the **third witness** ✓ (the ruling's word ✓) ✓ ⇒ ⇒ the 10 % tolerance ✓ is
  the declared slack ✓ and it is a **tokenizer-scale** slack ✓, not a measurement of the request ✓ ✓.

---

## 4. Executed agent-doings

- The checker's rule read ✓ (`tools/coverage_check.py:358-404` ✓) and the adapter's sidecar writer read ✓
  (`packages/hermes/live/__init__.py:789-830` ✓) ⇒ the plugin block's key set enumerated ✓ ⇒
  **`plugin.evictedTokens` is absent** ✓ ✓.
- **Five** synthetic sidecars derived from the real 0.13.21 capture ✓ (digest recomputed ✓, `traceFile`
  matched ✓) run through the checker ✓ ⇒ outcomes in §1 ✓ ⇒ ⇒ two reproducible holes ✓ ✓.
- The tolerance clause exercised at **50 %** and **5 %** off ✓ ⇒ live ✓ ✓.
- **No capture, no spend, no code change** ✓ — the variants live under `/tmp` ✓ ✓.
- Nothing of another lane's edited ✓; nothing pushed ✓.
