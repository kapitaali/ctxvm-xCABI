# RR-E2PILOT-REVIEW-20261121 — verified: E2 hosted answer-change pilot FAIL (2/5 clean), STOP; routing found, $3 ceiling never approached

Review lane, verify-then-record. Subject: staged `RR-E2ROUTE-20261121.md`, `RR-E2PILOT-PLAN-20261121.md`, and
`RR-E2PILOT-20261121.md` in the DSH sandbox staging area, plus the actual result object
`e2-pilot/e2-pilot-result.json`. Date 2026-11-21. The work is **sandbox-only**: the ctxvm repo is untouched by it
(HEAD `8e709c2`, only the pre-existing research WIP in the tree). No call, spend, landing, or push by this lane;
I did not clear staging (left for your copy, per your question).

## 1. Routing verified (from the staged card)

| route | endpoint / model | result |
|---|---|---|
| opencode-go / hy4-flash-free & gpt-6-luna | `https://opencode.ai/inference/go/openai/v1/chat/completions` | **HTTP 403, Cloudflare 1010** — unusable |
| opencode Zen / hy4-flash-free | `opencode run` | **429 FreeUsageLimitError** — quota exhausted |
| **OpenRouter / gpt-6-luna** | `https://openrouter.ai/api/v1/chat/completions`, model **`openai/gpt-6-luna`**, `OPENROUTER_API_KEY` | **HTTP 200**, echoed model, `PONG` — **primary** |
| **Nous / gpt-6-luna** | `https://inference-api.nousresearch.com/v1/chat/completions`, model `openai/gpt-6-luna`, `NOUS_ACCESS_TOKEN` | **HTTP 200** — **backup** |

The earlier Nous 401 was a wrong model id / direct-auth shape; the OpenAI-compatible path with `openai/gpt-6-luna`
works. This resolves the model/route conflict I flagged in `RR-E2PILOT-ROUTE-20261121.md` (the model was never
available under the literal id on `explabs`, but exists on both permitted routes as `openai/gpt-6-luna`). No key
values were recorded — only prefixes and env-var names.

**Cost correction, verified from receipts:** smoke rate **$0.0001395/req**, so the full 1,320-call cell projects
**~$0.18**, not the historical ~$11.37 — the W8-SPEND blended rate ($0.00861/req, `W8-SPEND:82`) is ~60× stale.
Pilot actual cost **$0.00575** against the $3 ceiling — never close. This is a receipt measurement, not a quote.

## 2. Result verified (from `e2-pilot-result.json`, not the card's prose)

| quantity | result object | matches card |
|---|---|---|
| `cleanN` | **2** | yes (fb03, fb04 clean) |
| `targetedRate` | **1.0** (15/15 targeted ablations changed the answer) | yes |
| `randomRate` | **0.933** (14/15 random removals changed it) | yes |
| `verdict` | **FAIL** | yes |
| `total_cost` | **$0.0057491** | yes |
| repeat-changed | fb01, fb02, fb05 → 3/5 | yes |
| route / model | OpenRouter / `openai/gpt-6-luna` | yes |

Per-item flags in the object: fb01/02/05 `clean:false` (repeatChanged true), fb03/04 `clean:true` — exactly the
card's table. **FAIL under the frozen criterion** (PASS = ≥4/5 clean AND targeted>random; FAIL = <4/5 clean OR
targeted≤random). Clean count 2/5 fails; targeted>random cannot rescue it. STOP observed: no rule loosening,
re-normalization, re-scoring, model switch, or full cell — the frozen anti-fishing path was followed.

## 3. Mechanism, honestly stated

The model **did** use the file content (all 15 targeted ablations changed the answer) — the failure is the
**instrument's specificity**: (a) at temperature 0, 3/5 baseline-repeat calls still returned a different answer
(hosted stochasticity — seed not honored or decoding nondeterminism), so ablation-induced changes on those items
are not attributable to the ablation; (b) 14/15 random-page removals also changed the answer, so a binary change
flag cannot distinguish the causally relevant page from a distractor. This is a **measurement-instrument finding**,
the hosted analogue of E0's gradability failure — different mechanism, same shape (instrument, not hypothesis,
failed). No causal-influence, paging, ρ, cost-saving (law 7), model-quality, or unscoped-determinism (law 8) claim.

## 4. Caveat I record, not overlook

The plan §3.1 required `debited_usd` (a provider invoice field); these APIs return **`usage.cost`** in the response
(OpenRouter `cost_details.upstream_inference_cost`; Nous `cost_details.source = "gateway_computed_spend"`) — a
provider-reported per-call cost, neither a post-hoc invoice nor `providerUsage` token estimates. The routing card
records this as an implementation interpretation, not a change to the frozen PASS/FAIL criterion; for a ~$0.006
pilot the risk is low. A future full cell may require invoice reconciliation — a fresh ruling, not assumed here.

## 5. State and applied

E2 remains HELD at $0; no full cell authorized. A retry (deterministic route or graded answer-similarity) would be a
**new deviation + fresh ruling** — not started. The repo is untouched by this work; research lane's v3 WIP and
staged prereg fold-in preserved; staging left for your copy. Applied: this card, an append-only LOG row (four
pipes), and a day-file section in `reports/RR-DAY-20261121.md`. No push.
