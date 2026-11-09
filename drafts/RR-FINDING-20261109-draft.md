# One finding from xCABI traces: a third of tool calls are repeats (single session)

We counted duplicate tool calls in one agent session trace (xCABI v0, 347 tool results, 21 turns). About a third of tool results repeat the exact same call (same tool + arguments): 124 repeats, 35.7% (Wilson 95% interval roughly 31% to 41%). In the public demo corpus (17 traces, 118 results) the pooled rate is much lower (5.9%), because most of those traces are scripted beats. The everyday session is noisier than the demos.

Why it matters without any paging claim: xCABI gives each tool result a content-addressed identity, so "same call again" is countable from the trace alone. This is a ledger finding, not a claim about waste or savings — a repeated call may be legitimate (state changed). We make no cost claim.

This is one session, one harness, one model. Do not generalise beyond single-source directional evidence.

Try it on your own trace:

```sh
python3 -c "import json,collections,sys; refs=[json.loads(l)['page']['id']['logicalRef'] for l in open(sys.argv[1]) if l.strip() and json.loads(l)['type']=='page.declare']; dup=sum(c-1 for c in collections.Counter(refs).values() if c>1); print(len(refs), len(set(refs)), dup, round(dup/len(refs),4) if refs else 0)" <trace.jsonl>
python3 spec/rfc-0/validate_schema.py <trace.jsonl>
./rust/target/release/replay <trace.jsonl>
```

Join us: emit xCABI traces (session.open, page.declare per tool result), share only counts plus validator/replay outputs, and we will compare methods. No raw traces needed.

---
Public-ready draft. Not posted, not sent. See reports/RR-FINDING-20261109.md for methods, limits, and mail version of the invitation.
