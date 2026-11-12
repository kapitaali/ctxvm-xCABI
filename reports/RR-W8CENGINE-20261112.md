# RR-W8CENGINE-20261112 — the review side's comments on the engine-layers diagnosis: sound, with one
## correction to this lane's own card, one cheap insurance left, and a third option (close the line)

Card: the review side's comments on the other lane's engine-layers diagnosis
(`reports/RR-W8C-ENGINE-LAYERS-20261112.md`, `d7716f9`) and on the state it leaves the lane in.

## 1. The diagnosis is sound, and the exclusion method is the right one

Every exclusion they list is a **file-level fact** ✓ — both homes' `context.engine` ✓, the profile's
config selecting a `CtxvmFaultPinEngine` ✓, plugin isolation `in_process` ✓, no duplicate YAML keys ✓
(the earlier warnings are from 11 November ✓), no `clone_for_agent` failure ✓, and the registration
logged at 14:18:47 — six seconds after the gateway started ✓. With those excluded, their reading of
`agent_init` is the right one ✓: `_select_context_engine(load_config_readonly())` can return None on three
paths ✓ (safe-worker mode ✓, `engine == "compressor"` ✓, or nothing matching in
`get_plugin_context_engine()` ✓), and only the third survives the evidence ✓ — **the disagreement is not
on disk, it is inside the agent build** ✓, i.e. the registry that carries the engine is empty *at
construction time* ✓.

**The "fourth form of the same failure class" claim is supported by the books' record** ✓, and the class
is worth stating precisely because the remedy differs by form ✓: the first three (the CLI path never
selecting ✓, the gateway not loading a profile's plugins until it restarts ✓, the profile home missing the
plugin module ✓) were all **configuration or ordering** faults with a known fix ✓; this one is a
**host-side ordering property** that no ctxvm-side configuration controls ✓ and no file records ✓ — which
is exactly why it is the first that configuration cannot fix ✓.

## 2. One correction to this lane's own card (erratum appended)

My card `reports/RR-VOIDPAIR-20261112.md` concluded that the treatment arm "never engaged the engine" on
the strength of the sidecar's `engine: null` ✓. **That inference was one step too strong** ✓: the field is
null iff the **selection count is 0** ✓ (`live/__init__.py:520`, `:534` ✓), so it establishes *"no
selection happened"* ✓, not *"`select_context()` was never called"* ✓. The **conclusion was right** ✓ and
the correct evidence is the **agent's behaviour** ✓ — it came up with the built-in compressor ✓, the
host's own fallback ✓ — and their later `engineRegistered` field is the proper discriminator ✓
(`93ff8ab` ✓). The erratum is appended to that card ✓.

## 3. They have already closed the sharp edge this lane raised

The arm-conditioned verdict — *"a treatment that never acted is void, not a control that behaved"* ✓ —
is **implemented** in `450b9bd` ✓, and the three layer fields (`engineRegistered`, `rootEngineSetting`,
`homeEngineSetting` ✓) are exactly the discriminator whose absence made the void ambiguous ✓ (with the
code comment stating both readings ✓). So the review side's §2 finding from the last card is closed ✓, and
the sidecar can now name **which layer** failed ✓.

## 4. The one cheap insurance left — and it is worth taking before any paid run

The VOID capture was **avoidable** ✓, and the reason it was avoidable is specific: the **probe's READY
runs in a different process/session than the 42-call run** ✓ ✓ — so a per-process registry emptiness hits
the *run's* process and not the probe's ✓ → "probe first" cannot guarantee the run's activation ✓.

With the three new fields, the insurance is now trivial and *immediate*: **the run should assert
engagement on its first prompt and abort** ✓ — the first prompt's sidecar distinguishes
registered? ✓ / configs say ctxvm? ✓ / selections > 0? ✓ and *names the layer* ✓ ✓. So a host-side
regression costs **one prompt** ✓ instead of 42 calls ✓ — and on a paid run, $0.00 instead of $0.25 ✓✓.
This is the same discipline the plan already states (*"a failed precondition is not a cell"* ✓); what is
missing is that the precondition must be checked **inside the run**, per process ✓, not only by a
separate probe ✓.

## 5. On the two ways forward

**Option 1 (instrument the host build ✓) — supported, and it is the right first move.** It is a
**diagnostic**, not a design change ✓; the consent framing is correct ✓ (the agent runtime is outside
both lanes' ownership ✓, so the owner is the right gate ✓); and it answers the right question ✓ — not
"what does the config say" (exhausted ✓) but **"what order"** ✓ — in one free prompt ✓ rather than another
guessed restart ✓. If it names the defect, the fix is the host's to propose ✓ and the books can record
the dependency ✓.

**Option 2 (bypass the host slot ✓) — endorse their own caveat, and price it as a different experiment.**
It changes the activation path ✓ → **the two booked cells would then be measured on a different mechanism
than any future one** ✓ (their words ✓), and it would make the *plugin* the selector rather than the
host's engine ✓ — a different claim ✓ about a different object ✓. It is not a fallback; it is a new
experiment with its own preregistration ✓, and it should be costed as one ✓.

**A third option, which the arithmetic supports ✓: file the host defect and close the W8C line.** The
remaining measurable upside of the whole line is ≈ **$0.009 per session** ✓ (3.5 % of one paid pair ✓ —
`reports/RR-POLICYCHOICE-20261112.md` ✓), while the blocker is **host-side** ✓ — so if option 1 does not
name it in one free prompt ✓, the engineering cost dominates the measurable value ✓ and the honest end
is to close the line with the defect filed ✓ and the *published* results standing ✓ (cell-02 ✓, the
paid cell-03 at **2.11×** ✓ with its cause measured ✓, the simulator's failure ✓, the paid bill
**$0.2534** ✓ — every attempt in between cost **$0.00** ✓ ✓).

## 6. What the books should add, whoever decides

The **host-activation dependency** belongs in the *pre-conditions* of any future cell ✓ — not in the
troubleshooting notes ✓: *"the host must build the agent with the plugin's engine visible in
`get_plugin_context_engine()` at construction time; the plugin cannot observe this from its own side, so
the run must assert it from the capture (first prompt) and abort if it fails"* ✓ ✓. That is the one
sentence that would have made today's void a one-prompt refusal ✓, and it is the class's fourth form
written down ✓.

## 7. Executed agent-doings

- The diagnosis was checked against the books' record of the failure class's first three forms ✓ and
  against the code for the `engine` field's true meaning ✓ (`live/__init__.py:520`, `:534` ✓) — which
  produced the erratum on this lane's own card ✓.
- The two new commits (`450b9bd` ✓, `93ff8ab` ✓) were read ✓ and the review side's earlier sharp edge
  was found **already closed** ✓, with the layer discriminator in place ✓.
- The remaining insurance was specified concretely ✓ (assert engagement on the first prompt, abort, name
  the layer ✓) and the three options were weighed against the measured upside ✓ ($0.009/session ✓).
- Kit: this card + the erratum on the void-pair card + LOG row + the day file + the roadmap's W8C
  pointer. No file of the other lane's edited ✓; no host-side byte touched ✓ (the owner's consent is the
  gate for that ✓); nothing pushed ✓.
