# RR-W8CTRANSPORT-20261112 — the review side's reading of the host's source completes the diagnosis:
## the selection hook has ONE production call site, the one-shot CLI is not a separate fast path, and the
## remedy is the desktop transport (which is the *scoring* remedy, not a comparable cell)

Card: the review side's comments on the other lane's engine-layers stop ("stopping the probing here") and
on the two ways forward. Every host claim below was read in the host's tree (read-only ✓ — no host byte
touched ✓).

## 1. The host's source completes the diagnosis — it is now a *precise* statement

Read in `~/.hermes/hermes-agent` ✓:

| host fact | locator | what it means |
|---|---|---|
| the per-turn selection hook has **exactly one** production call site | `agent/turn_request_assembly.py:145` ✓ (the only other reference is the definition at `agent/conversation_loop.py:1357` ✓) | if that site is not reached, the engine is never asked ✓ |
| its **only** guard is `_engine_overrides_hook(engine, "select_context")` ✓ | `agent/conversation_loop.py:1342-1354` ✓ → true iff the engine's `select_context` is **not** the ABC's no-op ✓ → our `CtxvmFaultPinEngine` overrides it ✓ → the gate passes ✓ (their log ✓) | the gate is not the obstacle ✓ |
| the one-shot CLI is **not** a separate fast path ✓ | `hermes_cli/main.py:2903-2911` ✓: `_run_oneshot_from_args` → `launch_gateway_chat` ✓ | the one-shot transport *does* go through the gateway's agent ✓ — so it *should* reach the same assembly ✓ |

⇒ **So the defect is not "the difference is in how the host assembles this path"** (a hypothesis ✓) but:
**the request in the one-shot path is not assembled through `assemble_api_request`**, which is the only
place the selection hook is invoked ✓✓. That is a **minimal, file-and-line reproducible** statement ✓ —
exactly what an upstream report needs ✓ — and it is *upstream's* to fix ✓ (the host's tree ✓).

## 2. Their `_entered.log` evidence is durable — checked, because it could have been an artefact

The plugin's prune (`live/__init__.py:268-278` ✓) globs **only `*.jsonl`** ✓ → it does **not** remove
`_entered.log` ✓ → and the file does **not exist** in the trace dir ✓ → so *"`select_context` was never
entered"* is solid ✓✓, not a retention artefact ✓. (The durable witness is the sidecar's **`engineEntered`**
✓ — 0.13.7 ✓ — which is per-session ✓ and survives ✓; the void runs were 0.13.3 ✓, which predates that
field ✓✓ — so the *current* instrument can answer the question directly ✓.)

## 3. The one free check that turns a hypothesis into a locating fact — and it is a *confirmation*, not a
## new experiment

The host's diagnostic is **already in the tree** ✓ (`agent/agent_init.py:1840-1851` ✓, marked *"ctxvm
diagnostic (owner-approved 2026-11-12)"* ✓) and prints, at agent build:
`build name='ctxvm' safe_worker=False` ✓ / `registry candidate=True name='ctxvm'` ✓ / `attached
before=NoneType selected='ctxvm'` ✓ / `attached after=CtxvmFaultPinEngine` ✓✓ — i.e. **the agent that is
built holds the plugin engine** ✓✓.

Their evidence already has those lines **and** the empty `_entered.log` **from the same sessions** ✓✓ →
so the tension is real and measured ✓: *the agent holds the engine, and the hook is never called* ✓✓.

**What remains to be pinned down is one line of fact** ✓: *which assembly path the one-shot request
actually takes* ✓ (the host's source narrows it to "not `assemble_api_request`" ✓✓, but the *exact*
path is what the report should name ✓). One session now ✓ — with the diagnostic in the tree ✓ and the
sidecar's `engineEntered` ✓ — reading **all three** witnesses from the same run ✓✓ (the diagnostic lines ✓,
`engineEntered` ✓, `_entered.log` ✓) costs **$0.00** ✓✓ (free tier ✓) and turns the report from
"the hook is not called in this path" into "the hook is not called in this path, and here is the path" ✓✓.

## 4. On the two ways forward — they are not exclusive, and one of them is the remedy

- **Option 1 (report upstream ✓) is warranted** ✓ — this is a real host defect ✓ (the per-turn selection
  hook is unreachable on the transport the CLI uses ✓✓) ✓ and it belongs to Hermes ✓✓. With §1's
  locators and §3's same-run witnesses, the report is *minimal and reproducible* ✓✓.
- **Option 2 (confirm the hook on another transport ✓) is worth doing, and it is not only a test** ✓✓ —
  it is the **remedy's first step** ✓: if the desktop path engages ✓, the **scoring** run can happen ✓✓
  (the simulator needs a scoreable capture ✓✓) with **no upstream patch** ✓✓ and **no change to the
  ctxvm instrument** ✓✓ — which keeps the two booked cells' instrument comparable ✓✓ (unlike the
  "bypass the host slot" option ✓✓, which changes the *mechanism* ✓).
  **The honest caveat** ✓: a pair run on the desktop path is a **different transport** ✓ → it would be a
  *new cell on a new transport* ✓, reported as such ✓, not comparable cell-to-cell with cell-02/03 ✓✓ —
  which is fine for the *scoring* purpose ✓✓ and not fine for a booked *cell* ✓✓.

## 5. A third step that is ours, cheap, and reusable

The run's **engagement check** (`5b3ffec` ✓) already reads the live stamp ✓ (`engine` /
`engineSelections` ✓✓) — so it can distinguish *"called but selected nothing"* from *"never called"* ✓✓
today. The refinement worth making ✓: when the transport never calls the hook ✓, the refusal should
**say so** ✓ — *"this transport does not assemble the engine"* ✓✓ — instead of producing a void ✓✓, and
that refusal is the **reusable artefact** ✓ (it would have said this on 11 November ✓✓).

## 6. My recommendation, in order

1. **The one free session** ✓✓ (§3 ✓) — it costs $0.00 ✓, it confirms the tension ✓, and it makes the
   upstream report exact ✓✓. No host patch is needed for *this* ✓ (the diagnostic is already in ✓✓).
2. **File the upstream report** ✓✓ with §1's locators ✓ and §3's witnesses ✓ — a minimal reproducible
   report ✓ (the hook's single call site ✓, the guard ✓, the transport ✓).
3. **Try the desktop transport** ✓✓ — as the **scoring** remedy ✓✓ (a scoreable capture without an
   upstream fix ✓✓ and without touching the instrument ✓✓), reported as a different transport ✓✓.
4. **If the scoring run lands** ✓✓, close the W8C line on its own terms ✓✓ — the measured results stand ✓
   (cell-02 ✓, the paid cell-03 at **2.11×** ✓ with its cause measured ✓, the simulator's failure ✓,
   the paid bill **$0.2534** ✓, every attempt since at **$0.00** ✓✓).

## 7. Executed agent-doings

- The host's tree was **read** (read-only ✓ — no host byte touched ✓, no consent needed for reading ✓✓)
  and four facts were established ✓: the hook's single production call site ✓, the guard's exact
  condition ✓, the one-shot CLI's route through `launch_gateway_chat` ✓✓, and the prune's `*.jsonl`-only
  glob ✓✓ — which is what makes the empty `_entered.log` reliable ✓✓.
- The host's diagnostic output at 15:19:50 and 15:24:20 today was read ✓✓ and shows the agent holding
  the plugin engine ✓✓ — with the *same sessions* also showing the hook un-entered ✓✓.
- The trace dir was checked for `_entered.log` ✓ (absent ✓ — and the prune does not remove it ✓✓), and
  the sidecar's `engineEntered` ✓ was identified as the durable witness ✓✓ (added in 0.13.7 ✓; the void
  runs were 0.13.3 ✓✓).
- Kit: this card + LOG row + the day file + the roadmap's W8C pointer. No host byte touched ✓; no file of
  the other lane's edited ✓; nothing pushed ✓.
