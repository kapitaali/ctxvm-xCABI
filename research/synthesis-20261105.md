# Research synthesis — ctxvm against the three safety questions (2026-11-05)

**Provenance.** Two research notes were written independently (different models, same owner prompt)
about what ctxvm can and cannot contribute to dangerousness testing, legibility, and control. Both
sources stay on disk under `research/uncommitted/` (gitignored, 2026-11-05, owner decision): the
convergence of two independent readings is itself the finding, so the committed record is this
synthesis, not the sources.

- `research/uncommitted/research-note.md` — agent memo (behind it, the committed full note of
  `a0af4c7`: `research/safety-and-auditability.md` + `sources-reviewed.md`).
- `research/uncommitted/ctxvm and AI safety research note and proposed white-paper sections.md` —
  second note, by a different model.

## 1. The merged thesis

Both notes reach the same position independently: ctxvm is not an evaluation method, an
interpretability tool, or an alignment technique. It cannot tell you a model is dangerous, see
inside it, or make it behave. What it supplies is the **exact, replayable input side of every one
of those problems** — and the literature shows that input side is a standing gap: evaluators,
monitors, and control protocols are all defined over agent trajectories and transcripts that few
of their methods record in a portable, reproducible way. The white paper's own seed (§3.11,
`research/white-paper/white-paper.md:252` — "the trace reveals not just what it did but what it
saw") is the right size for this, and both notes say the paper's abstract overstates it.

## 2. Where the two notes agree

| Point | Agent memo | Second note | Locator check |
|---|---|---|---|
| The did/saw distinction is the seed | argument throughout, §1–3 | "Section 3.11 contains the seed idea" | ✓ `white-paper.md:252` |
| The abstract's "everything depends on knowing what the model saw" needs the necessary-not-sufficient form | framed honestly in §2/§3 | explicit proposed edit to abstract + conclusion | ✓ the sentence exists twice: `white-paper.md:17` and `:268` |
| Tamper evidence is a field-wide gap; a per-file checksum is not it against an agent with write access | arXiv:2606.04990 named as the field-wide statement | §5-1 threat model, hash-chained events or signed roots | ✓ — and a **third site**: `white-paper.md:258` already calls the checksummed trace "tamper-evident", which this claim challenges |
| A coverage manifest per evaluation run (tools loaded, scope, effect classes, monitors) | card 2, with the live capture's own numbers (`toolSchemas: 21`, `requestChars: 1,628,596` per turn) | §5-3 evaluation infrastructure + HAL (arXiv:2510.11977) scaffold sensitivity | convergent |
| Honest cannot-do list | cannot define dangerousness, cannot detect sandbagging, cannot see weights, cannot guarantee alignment | cannot see internals, cannot detect deception, a trace is not a cause, plus the **false-confidence risk** | unions cleanly |

## 3. Where they complement each other

The agent's note contributes the failure-mode literature and the concrete missing features: UK
AISI's cheating evaluations (models cheat, then do not reliably self-report it — detection needs a
monitor over the full trajectory), AISI's post-incident synchronous monitor as a requirements list
for what a control surface records, and four cards cheapest-first: record refusals with the policy
version ("didn't try" vs "was stopped" are indistinguishable today), a coverage manifest per eval
run, a monitor-replay harness reporting TPR/FPR over recorded traces, and claim-to-page evidence
with provenance classes.

The second note contributes the experiment agenda and the paper structure: context policy is part
of the scaffold (no study measures dangerousness scores under a context-policy change — replay is
built for exactly that); evaluation-awareness trace diffs (which pages give an evaluation away);
page-level ablation against the identifier touch ratio (ContextCite-style, arXiv:2409.00729) — the
first study that would supply ground truth for the fault-recall metric; page provenance à la CaMeL
(arXiv:2503.18813); Ctrl-Z resampling (arXiv:2504.10374) as a consumer of W12's copy-on-write
branching; and ten proposed white-paper sections with a ranked research agenda.

**The reconciliation the synthesis adds:** "monitor harness" means two different things in the two
notes, and the difference is the project's own determinism boundary. The agent's TPR/FPR-over-
recorded-traces is deterministic — byte-replay over `corpus/m1–m8`, exactly what the core guarantees.
The second note's interventions (hint injection, page removal, ablation) put the model in the loop
and are non-deterministic by construction. So the harness is **two tiers**: tier 1, monitors scored
over frozen traces inside the core; tier 2, an experimental runner outside the core, runs marked
non-deterministic. The strongest candidate for the first tier-2 experiment is the second note's:
page-level ablation on real OpenCode and hermes traces against the touch ratio, which would both
strengthen the profiler and fix the fault-recall metric's ground-truth problem.

## 4. Verification ledger

- **Cross-checked by a reading lane this session:** FACE-Eval (arXiv:2608.29464) — abstract fetched
  and confirmed: "Chain-of-Thought Faithfulness of Reasoning Models Varies with Where and How
  Preference Cues Are Delivered" (29 Aug 2026); 5,100 samples; lower verbalized commitment for
  tool-return cues on **all 15 models**; higher unverbalized adoption on all 15; monitoring-awareness
  prompts do not reliably close the gap; monitor detection r = −0.54 / −0.78 across 32 cells.
  The agent's memo quoted it accurately. This is the strongest single tie in either note — **the
  tool channel is where self-report is least faithful, and tool returns are the one surface ctxvm
  records natively** — and carries the paper's own scope caveat: a single-call, prefilled-tool setting.
- **Agent-primary, not cross-checked here:** the 55.4% divergence / 11.8% figures (arXiv:2603.26410);
  the UK AISI quotes; the 11.3 h vs 270 h capability swing — the agent itself marked that one UNVERIFIED
  (secondary-only read of Figure 1).
- **Inference, flagged by its own author:** the Ctrl-Z statelessness point (arXiv:2504.10374).
- **Kept as explicitly unread:** arXiv:2601.21112 (cited in the second note but marked UNVERIFIED),
  and the two follow-up papers (2603.00829, 2608.00583).
- **Kept as a to-do:** the EU AI Act application-date discrepancy for Art. 12 / Annex III systems —
  sources disagree (2 August 2026 vs 2 December 2027); check the legal text before citing a date.

## 5. Card queue (ranked)

1. **White-paper claim edit** (this card): weaken `white-paper.md:17` and `:268` to the
   necessary-not-sufficient form; qualify the "tamper-evident" sentence at `:258` (checksums prove
   bytes unchanged since write — tamper-evidence only against parties without write access; the
   stronger mechanism is unbuilt).
2. **Coverage manifest per evaluation run** — packaging card: the raw material already lands
   live (W13 prefix, W14 environment id, W15 effect classes); a manifest that says what a captured
   run was instrumented with is the cheap, measurable version of the manifest both notes asked for.
3. **Monitor-replay harness, tier 1** — TPR/FPR for a monitor scored over recorded `corpus/m1–m8`
   traces; deterministic, cheap, unblocks the measurement.
4. **Tier-2 runner (design note first, W16 precedent):** interventions (hint injection, page
   removal, ablation vs touch ratio) outside the core, runs marked non-deterministic; the fault
   taxonomy's ground-truth question rides on it.
5. **Design notes (owner-gated before any implementation):** refusals + policy version on the trace
   surface (additive, version-gated; audit-only non-claim); page provenance/trust attributes;
   paging as an attack surface (adversary-forced evictions); tamper-evidence options.
6. **Adjacent engineering card already recorded:** collide-proof trace filenames
   (`research/RR-LIVE-20261104.md` correction — reused trace names silently replace earlier bytes).

## 6. What the synthesis does NOT claim

ctxvm does not answer the three questions. A manifest does not make an evaluation valid; a watchful
annotation from a page table is not a prosecution; and recorded input is correlation-grade evidence.
The cannot-do lists in both notes stand verbatim, and the false-confidence risk the second note
names is real: a replayable record invites over-trust of its own completeness.
