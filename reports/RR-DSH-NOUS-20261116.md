# RR-DSH-NOUS-20261116 — the Nous route through dsh: the credential path, the probe, and the rate limit

Lane: review (verify-then-record). This card documents the 2026-11-16 investigation that blocked acceptance #4
of the dsh lane (W22). It changes no code, no spec, and no config in this repo. Times are UTC unless marked local
(local = UTC+2). Every number carries the command or log that produced it. Values of tokens and keys are never
printed; only names, equality checks, timestamps, and error codes appear here.

## 1. Questions

1. Is the Nous credential accepted on the dsh web route, and why did the first attempt fail?
2. Can the dsh headless app use the same key? (The probe.)
3. Can acceptance #4 (the mirror-mode on/off proof, `handoffs/05`) run now?

## 2. Answers, as of 2026-11-16 12:45Z

| question | answer | evidence class |
|---|---|---|
| Q1: is the key accepted on the web route now? | **Inferred yes.** The web session's turn 16 (12:30:30Z) returned 401 `AUTH` ("Your API key is invalid"). After the re-import at 12:34:20Z, turn 17 (12:35:06Z) returned 429 `RATE_LIMIT`. A 429 is returned after authentication. **No completed Nous turn is recorded** in the log. | measured error codes; the "after authentication" step is an inference, UNVERIFIED as a provider statement |
| Q1: why did the first attempt fail? | The dsh store's copy was **stale**. Before the re-import, `NOUS_ACCESS_TOKEN` in the store did not equal Hermes's current `providers.nous.access_token` (sha256 equality, 12:33Z). | measured (equality); the copy path is from source |
| Q2: can the headless app use the key? | **Not yet.** The headless process resolves `apiKeyEnv` from the **environment**. With the env var unset (run 2) the error names it; with `apiKeyEnv` removed (run 3) pi-ai reports no key at all. | measured (runtime error text, runs 2 and 3) |
| Q3: can acceptance #4 run? | **No, as configured.** `test-headless` (the only headless-app profile) has **no ctxvm bundle**, so an on/off pair there proves nothing. | measured (`--dump-config`) |

## 3. Timeline (UTC)

| time | event | evidence |
|---|---|---|
| 12:07 | probe run 1, profile `web` (local 14:07). CLI error, no session written. | probe dir `dsh-probe-web-20261116T140700`; stderr `error: too many arguments … got 2: headless, Reply…` |
| 12:12 | probe run 2, profile `test-headless` with an overlay that had `apiKeyEnv: NOUS_ACCESS_TOKEN`. `MISSING_CREDENTIAL`: the variable is not set in the process. | session `3b68866e-5e38-4d63-8368-85355c844671`; 0 usage records |
| 12:30:10 | probe run 3, same overlay without `apiKeyEnv`. `PI_AI_ERROR: No API key for provider: nous`. | session `830bc015-3be6-40c3-b913-11f552de5424`; usage 0/0/0 |
| 12:30:30 | web turn 16: `401 AUTH`, "Your API key is invalid, blocked or out of funds". | web session `36c3f9df-9839-48c9-9860-bae1f3b92fb9`, turn 16 |
| 12:30:53 | Hermes Nous token obtained (`obtained_at`); expires 13:30:53 (`expires_in` 3599). | `~/.hermes/auth.json`, `providers.nous` time fields |
| 12:33:44 | store-vs-Hermes equality check: the store copy did not match. | the equality check in §4 |
| 12:34:20 | `~/.dsh/.credentials.yaml` rewritten (the owner's `setup:hermes` re-import). | `date -u -r` on the store |
| 12:35:06 | web turn 17: `429 RATE_LIMIT` on the first attempt. Five retries; last error `retry_after` 10276, alternates listed. | web session, turn 17 |

Earlier turns in the same web log (upstream idle timeouts, earlier 401s and 429s) are not part of this timeline.

## 4. Measured facts, with commands

**Hermes Nous document.** `~/.hermes/auth.json` has `providers.nous` (access token, refresh token, agent key,
expiry fields) and a `credential_pool.nous` entry with `last_status: ok`. Field names and time fields only:
`python3` reading the file and printing keys whose names contain `expires`, `obtained`, or `_at`.
- `access_token` equals `agent_key` (sha256 equality). So the "wrong token kind" hypothesis is out.

**Store vs Hermes (sha256 equality only, 12:33Z, before the re-import).**
- store `NOUS_ACCESS_TOKEN` vs `providers.nous.access_token`: not equal.
- store vs `credential_pool[0].access_token`: not equal.

**Import path.** `~/Apps/deepseek-harness/scripts/import-hermes-credentials.ts`:
- line 194: `const token = record['access_token']`; line 197 maps it to `${NAME}_ACCESS_TOKEN` (for Nous, `NOUS_ACCESS_TOKEN`);
- lines 259–260: `storeConnectionKey(provider.ref, provider.token, …)` runs for each Hermes provider with no existence check.
- The body of `storeConnectionKey` is defined elsewhere and was **not read**. "Overwrites on every import" is therefore
  UNVERIFIED as a code fact. The observed change (401 → 429 after the 12:34:20Z rewrite) is consistent with it.

**Which app boots which profile.** `node apps/cli/lib/bin.js --dump-config --profile <p>` (boot-free):
- `web` and `nvidia`: `dsh-web-app`.
- `test-headless`: `dsh-headless`, and no `@ctxvm/dsh` bundle.
- The headless app's usage is `dsh --profile <name> "<task>"`; its help text is printed by `--profile test-headless --help`, which runs no task.

**Runtime errors, verbatim except masked values.**
- run 1: `error: too many arguments. Expected 0 arguments but got 2: headless, Reply with the single word OK…`
- run 2: `MISSING_CREDENTIAL: llm-pi-ai: no credential for provider route "nous"; its profile resolves NOUS_ACCESS_TOKEN, which is not set — store NOUS_ACCESS_TOKEN through the credentials service (the web Models page writes it) or export it, and remove apiKeyEnv only if this provider should authenticate from pi-ai`
- run 3: `dsh: PI_AI_ERROR: No API key for provider: nous`

**Spend.** Every failed attempt recorded zero tokens: run 2 has no usage record; run 3 has `inputTokens 0,
outputTokens 0, totalTokens 0`; web turns 16–17 show `usage(in=0,out=0)` on every attempt. Run 1 wrote no session.
No token was billed in the timeline above.

**Rate limit, turn 17.** Six attempts (one plus five retries). Retry delays, from the `llm/retry` event times:
about 0.47, 0.97, 2.0, 4.1, and 7.5 s, about 15 s in total. The 429 body gave `retry_after` 10276. Earlier 429 turns in
the same log gave 5468 (turn 12) and 5339 (turn 13). The retry delays do not follow `retry_after`. The code path
that chooses them was not read.

## 5. Corrections to earlier statements (this lane's books and advice)

1. **"`apiKeyEnv` is a credential ref resolved from the store, not the process environment."** Wrong for the
   headless app. The run-2 error text shows the environment lookup. The web app does read the store (the owner's
   re-import changed its outcome). Corrected in `RR-DAY-20261115` (commit `71c310f`).
2. **"Run the pair with `--profile web headless "…"` or `--profile nvidia headless "…"`."** Wrong. Both profiles boot
   the web app, which takes no task arguments. This advice is in my earlier replies and in `handoffs/05`. **The
   scaffold copy of `handoffs/05` still carries it.** The dsh lane should correct it.
3. **"The import overwrites unconditionally."** Unverified as a code fact (§4). The observed token change is consistent with it.
4. **"The retry backoff ignores `retry_after`."** Measured only: the delays do not follow `retry_after`. The code path was not read.
5. **"The 429 proves the key was accepted."** An inference from the error codes, not a provider statement. A
   completed Nous turn is what would prove it, and none is recorded.
6. **The owner's report "it worked."** The log shows the 401 became a 429, which means authentication passed. No
   completed turn is recorded. The card says "accepted (inferred)," not "turn completed."
7. **The probe's first verdict, `NO_SESSION`, for a CLI error.** Fixed: a `CLI_ERROR` verdict is now returned.
   `UNKNOWN` was returned for the no-key and rate-limit cases. Both now have rules.

## 6. The probe

- Script: `/tmp/opencode/dsh-probe-nous.sh`, sha256 `233760cc…`. Overlay: `/tmp/opencode/dsh-probe-nous-overlay.yml`,
  sha256 `9b44f779…`. Both are outside the repo and not committed; the dsh lane can move them into its scaffold.
- The overlay gives the nous provider (no `apiKeyEnv`) and sets `agent-default-model` to
  `nous / google/gemini-4-hydrogen`.
- Modes: `--check` (boot-free; verifies the composed config routes to nous) and the probe (one turn, hard
  timeout 150 s, no retries from the script).
- Verdicts: `PASS`, `CLI_ERROR`, `NO_SESSION`, `CREDENTIAL_MISSING`, `NO_KEY_VISIBLE`, `AUTH_REJECTED`,
  `NOT_FOUND_ACCOUNT`, `FORBIDDEN`, `KEY_ACCEPTED_RATE_LIMITED`, `TIMEOUT`, `UNKNOWN`.
- Free tests: `--check` passes. Synthetic classifier cases give the expected verdict for PASS, CLI_ERROR,
  CREDENTIAL_MISSING, TIMEOUT, NO_KEY_VISIBLE, and KEY_ACCEPTED_RATE_LIMITED.
- Live runs: three (runs 1–3). **No live run has returned PASS.** The PASS path is untested.

## 7. Open items

| # | item | owner | status |
|---|---|---|---|
| 1 | Confirm a completed Nous turn on the web route once the rate limit clears (send "Reply OK"). | owner | open |
| 2 | Headless probe: export `NOUS_ACCESS_TOKEN` into the launch environment from the current value. This must run within about an hour of the Hermes token's issue, and I will not read the token from the store. | owner, then one probe turn | open |
| 3 | The dsh store copy is a one-time import and goes stale hourly. A refresh path is an owner and dsh-lane decision. | owner / dsh lane | open |
| 4 | The runtime should honour `retry_after` rather than its fixed backoff. | dsh lane / owner | open |
| 5 | `handoffs/05` (scaffold copy) carries the wrong `--profile … headless` form. Correct it. | dsh lane | open |
| 6 | Acceptance #4 needs a headless-app profile with the ctxvm bundle installed. | dsh lane / owner | open |
| 7 | Three committed LOG rows from other lanes carry five pipes instead of four: `RR-W22-20261115`, `RR-W22CI-20261116`, `RR-POLICY-20261116`. Not edited (append-only). An erratum row is the fix if the review lane confirms it. | review lane | open |
| 8 | UNVERIFIED: the unit of `retry_after` (probably milliseconds, about 10.3 s); whether a 429 follows authentication; whether the 11:20 `deepseek-official` failure is the same env lookup (not probed). | — | open |

## 8. Reproduction

```sh
# Hermes Nous document: field names and time fields only
python3 -c "import json,os; p=json.load(open(os.path.expanduser('~/.hermes/auth.json'))); print(sorted(p['providers']['nous'].keys()))"

# store vs Hermes: equality only (values never printed)
python3 - <<'PY'
import json, re, hashlib, os
H = lambda s: hashlib.sha256(s.encode()).hexdigest() if s else None
h = json.load(open(os.path.expanduser('~/.hermes/auth.json')))['providers']['nous']['access_token']
t = open(os.path.expanduser('~/.dsh/.credentials.yaml'), encoding='utf-8').read()
m = re.search(r'(?m)^\s+NOUS_ACCESS_TOKEN:\s*(\S+)\s*$', t)
print('store == hermes access_token:', H(h) == H(m.group(1) if m else None))
PY

# which profile boots which app (boot-free)
cd ~/Apps/deepseek-harness && for p in web nvidia test-headless; do echo "$p: $(node apps/cli/lib/bin.js --dump-config --profile $p 2>/dev/null | grep -o 'patched by @deepseek-ai/dsh-[a-z-]*' | sort -u | head -2 | tr '\n' ' ')"; done

# the probe's free check (no spend)
bash /tmp/opencode/dsh-probe-nous.sh --check
```

The live probe is `bash /tmp/opencode/dsh-probe-nous.sh` and spends one turn. It is not part of the reproduction above.

## 9. Commits from this investigation

Day-file and probe-diagnosis commits, all on `main`, all unpushed: `e1dbaed`, `71c310f`, `001f3ca`, `17a4ade`,
`a2906e5`. Earlier the same day, this lane's dsh-side work: `11e0b81` and `f470d35` (handoffs 01 and 02),
`254fa7c` and `46171e1` (handoffs 04 and 03), `034f5a8` (day file), `fbf5009` and `a2c6559` (the #4 block analysis).
Full list: `git log --oneline` from `9a87ba2` on.
