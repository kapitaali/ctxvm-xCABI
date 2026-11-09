# RR-LESSONS-20261109 — what this card taught, and where each lesson now lives

Card: documentation only. No code, no spend. The durable lessons from the W8 instrument work and the
T-A task design, recorded in the place a future session will look for them.

## Into `controlled-agent-experiments` (skill, 3 patches)

**1. A witness must be attached to the object that does the work.** Three consecutive witnesses failed
the same way:

```
construction   `engine` was filled by an unconditional build_engine() at load,
               so it read "ctxvm" on a naive arm
module counter a flat sibling import (`from helper import ACTIVATIONS`) resolves
               through sys.modules by bare name, so both profiles shared one
               object — a naive session read 1 right after a paged one
instance count the host deep-copies the engine per agent (clone_for_agent), so the
               clone incremented its own copy while the plugin read the original:
               engineSelections 0 on a 14-read treatment cell that was running
```

The repair for each: read activation rather than construction; put the count on the registered object;
and make a mutable meter that `__deepcopy__` **shares**. The general rule is in the skill now, with the
measured symptom of each.

**2. A probe proves the build is live; only a cell proves the arm engages.** A one-line request never
reaches the treatment hook — nothing to select — so `engineSelections: 0` on a trivial probe says
nothing about activation. Probes answer: which plugin version the process loaded, where the capture
landed, which model and provider the record names. Engagement comes from a real cell.

**3. The arms can take different routes.** Control: 5 calls, 73k input, one `execute_code` call, never
holding the fixture. Treatment: 7 calls, 448k input, by reading. `NTR = -5.11` is the ratio between a
code shortcut and a read-heavy run. Any computational answer is short-circuitable by a code
interpreter, exactly as the earlier attempt was by content search. Record the declared tool refs per
cell, print the mix, refuse to compare cells whose mixes differ, and pin the surface before spending.

**4. Corrected an actively wrong instruction.** The skill previously said `ctx.get_config("<key>")`
returns the serving profile's value. It does not — it reads
`plugins.entries.<plugin_id>.settings.<key>`, and returned null for a profile whose config says
`ctxvm`. That advice is now a warning, with the measurement.

## Into `handoff/LANES.md` and `AGENTS.md` (earlier today)

Lane ownership, the four shared-file rules, and the reason `experiments/` is ignored pending
publication. Those are repo conventions, not experiment design, so they live in the repo.

## The shape of the whole failure, stated once

Every defect this card found was a **measurement of the wrong object**: an engine that was built
rather than used, a counter in a shared module rather than on the engine, a clone rather than the
original, a checker reading a reference rather than the artefact, a probe rather than a cell, a
naive run using code rather than the treatment run reading. None of them was a bug in the thing being
measured. That is the single line worth carrying forward: before trusting a number, ask which object
produced it and whether that object is the one that did the work.
