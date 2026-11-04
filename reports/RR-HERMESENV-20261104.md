# RR-HERMESENV-20261104 — the hermes lane derives W14's environment id

**Card:** job 2 of the 2026-11-04 handover. **Status:** landed; `ALL GATES GREEN`. Plugin 0.8.0.
**Outcome:** the `(unknown)` bucket in `ctxvm stream` was not a permanent fact — the host exposes the
session's workspace to a plugin handle, so the id is derived rather than declared absent.

## 1. The question the card asked

`06f6b6b`'s first run put six hermes sessions into `(unknown)`. W14 said the hermes gateway cannot
derive an environment id because the plugin runs in the gateway process, whose `cwd` is not the
session's project. This card asked what the gateway actually exposes, and to either wire a
non-secret derivation or land the absence as the record.

## 2. What the host exposes — audited, with locators

| Surface | Workspace fact? | Locator |
|---|---|---|
| hook payloads (`on_session_start`, `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `pre_api_request`, `on_session_end`) | **no** — none carries a path | payload keys read in `agent/turn_context.py:810-824`, `agent/turn_api_request.py:60-79`, `hermes_cli/hooks.py` `_DEFAULT_PAYLOADS` |
| shell-hook stdin JSON | yes, but `Path.cwd()` — the **process** cwd | `agent/shell_hooks.py:88-99` |
| plugin handle | **yes: `ctx.session_cwd()`** | `hermes_cli/plugins.py:605`, backed by `hermes_cli/plugin_session.py:48-51` |

`plugin_session.py`'s module docstring is decisive: "Plugin hooks and tools run in the gateway
process, whose own cwd is the install root and is shared by every session (it is never `os.chdir`-ed).
These read the calling session's key, client surface and recorded working directory instead." And
`session_cwd()` is documented as "never the gateway process's own cwd".

So the fact exists; it simply arrives through the handle rather than the payload.

## 3. What landed

- `_derive_environment_id(cwd)`: `env-` + 12 hex of `sha256("remote:<normalized>" | "path:<abs>")`.
  Only the digest is emitted.
- `_session_environment_id(session_id)`: explicit `CTXVM_ENVIRONMENT_ID` wins; otherwise the host's
  recorded workspace, cached per session; empty string → **absent**, never a hash of nothing.
- The adapter stamps `environmentId` onto the payload at the top of every handler, because
  `on_session_start` does not fire in this build — whichever hook creates the tracer must carry it.
- The plugin's per-session `TraceInit` now carries `environmentId` from the identity dict, so one
  multiplexed gateway can hold sessions from different workspaces.

## 4. Normalization had to change, and both lanes had to change together

The first implementation produced different ids for the same repository over https and ssh, because
the scheme survived normalization in one path and not the other. The rule is now identical in both
implementations: drop scheme, drop userinfo, first `:` → `/`, drop `.git`, lowercase.

```
https://user:token@host/Org/Repo.git  ─┐
git@host:Org/Repo.git                 ─┴→ host/org/repo → env-<12 hex>
```

A test asserts the two transports agree, that a different repository differs, and that neither the
host name nor the token appears in the id.

## 5. Verification

```
pytest packages/hermes   112 passed (was 111 before this card's four new tests, 108 at handover)
node --test packages/node 21 passed
bash tools/run-ci.sh      ALL GATES GREEN
```

Cross-lane agreement, checked directly rather than assumed:

```
python  _derive_environment_id("/home/theb/Documents/ctxvm")  → env-2b4652ae9d98
node    deriveEnvironmentId("/home/theb/Documents/ctxvm")     → env-2b4652ae9d98   AGREE
```

End to end: a capture driven with `session_cwd = /home/theb/Documents/ctxvm`, then the stream view:

```
environment env-2b4652ae9d98
  started              turns  pages  shown  unshown  faults  residTokens  file
  2026-11-04T10:57:01Z     0      1      0        1       0            2  e2e.jsonl
  summary: 1 session(s), …
```

The `(unknown)` bucket is gone for a hermes session that has a recorded workspace.

## 6. What is still honest about it

- A session the host records no workspace for still lands in `(unknown)`. That is correct, and the
  test pins it.
- `session_cwd()` falls back to the profile's terminal cwd when a session records none
  (`plugin_session.py:36-42`). The id then names the profile's default workspace, not necessarily the
  project. It is the host's own declared working directory for the turn, which is what "environment"
  means operationally — but it is not proof that the session edited that repository.
- The existing six live traces keep their `(unknown)` grouping: they were captured before this change
  and traces are append-only. Only new sessions carry the id.
- One `git config` subprocess per workspace directory, cached, 1.5 s timeout, skipped when git is
  absent. It runs when a session's tracer is created, not per event.

## 7. Follow-up worth doing (not done here)

`ctxvm stream` could print the environment **name** alongside the id when a local directory matches
the digest — but that would require scanning the filesystem for candidates, which is inference in the
other direction. Left out deliberately.
