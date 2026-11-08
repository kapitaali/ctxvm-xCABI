# WORKFLOW — how the repo agent and the external reviewer collaborate

Owner runs OpenCode and Hermes Agent daily; Claude reviews in chat sessions that start fresh each time. This file is process law for both sides, subordinate to `08-HANDOFF.md` (process) and `08.1-UPDATE-PROMPT.md` (integrity + approval gates).

## Session start
1. Owner runs `bash tools/session-start.sh <packet-number> [--with-context]` (POSIX sh, coreutils only). It writes `handoff/SESSION-START.md` = `handoff/PROJECT-STATE.md`, plus `handoff/CONTEXT-PACK.md` when `--with-context` is passed, plus the named packet `handoff/packets/P<n>-*.md`. It prints byte counts and fails past 16 KB, naming the part to cut.
2. Owner pastes `handoff/SESSION-START.md` into the chat. No other context is required.

## During a session
- The reviewer handles: design and claim review, prompt writing, decision framing, and checking an experiment design before it spends money.
- The agent handles: bulk reading, literature sweeps, drafting long documents, running tests and gates, git work, and citation verification with recorded locators.
- Nothing goes to the reviewer unverified: the agent re-derives numbers with repo commands and cites the report path before sending. Excerpts carry file path + line range and their provenance (committed HEAD vs working-tree WIP).
- Both directions ask for diffs or patch lists, never whole rewrites (token cost and review quality).
- Secrets/content law for packets: no prompts, no trace bodies, no credentials, no absolute home paths in any handoff file; use hashes, counts, redacted excerpts; data that has not left the machine must not be quoted.

## Session end (per deliverable, standing instruction for the agent)
1. Write a state delta of at most 150 words (what changed, what is next, what is open) and apply it to `handoff/PROJECT-STATE.md` (update the header date + agent + the "after <work item>" line).
2. If the item raised a question for the reviewer, add it to `handoff/QUESTIONS.md` with its packet number and status; create or update a packet under `handoff/packets/` when a chat answer is needed.
3. Run `bash tools/check-handoff.sh`; fix every failure before reporting (existence, byte limits: PROJECT 6 KB, CONTEXT 8 KB, WORKFLOW 4 KB, QUESTIONS 3 KB, each packet 3 KB; required headings; secret-shape scan that never prints matched bytes).
4. Repo book law still applies for anything committed: one card = one report `reports/RR-*` + one append-only LOG row + a day-file section; gate green before the commit, signed kapitaali.

## Approval gates that survive every session
No publishing, no submission, no renaming, no unsealing `spec/rfc-0/`, no plugin-default changes, no money beyond the owner-set cap, no real-session content leaving the machine — owner decision each time (08.1 §3). Pushes are the owner's act.
