"""W8 v1 ``FaultPinPolicy`` context engine — the paged arm's control plane.

Design: ``design/w8-capture-design.md`` §3.3/§4 (preregistered; after the first
run, that file changes nothing). The engine enforces the virtual budget
``vBudget`` by SELECTION (``select_context``), never by compaction:
``should_compress()`` is always False, ``compress()`` implements the abstract
contract only, and ``prune_tool_results_only()`` stays the preregistered no-op
so the two seams cannot double-apply inside one capture (§4).

IMPORTANT, measured 2026-11-06 (RR-ENGINEGAP-20261106): at the preregistered
vBudget of 24,000 the engine is a NO-OP on long sessions. `_plan` returns early
when the protected floor (system prompt + protect_first_n head + protect_last_n
tail + pinned pages) already exceeds vBudget, and six real tool results exceed
24,000 tokens on their own. A live capture shipped 358,616 tokens with the
engine attached: no selection, and compaction disabled by `should_compress()`
returning False, so nothing bounded the context. Raise `CTXVM_VBUDGET` for real
traffic, or keep the compressor. The engine also emits no record of what it
selected — a gap, not a feature.

--------------------------- the seven laws ---------------------------
L1 (ordering, §3.3): the selected request runs (a) the system prompt verbatim
    FIRST, (b) the head-protected messages (stock ``protect_first_n`` counts
    non-system head messages kept verbatim), (c) the pages pinned by faults in
    first-pin order — a newly pinned page APPENDS after the pinned block, and
    pinned order stays frozen for the session —, then (d) the remaining kept
    content in transcript order (the recency tail). A page pulled into the
    block is REMOVED from its transcript position by rewriting its call entry
    out of a COPY of the producing assistant message, so no call id exists
    twice and no tool reply dangles.
L2 (purity): selection is a pure function of (page-table state, vBudget). The
    page table advances only through digest-keyed, idempotent credits — a
    provider retry re-observes the same texts as the same digests, so the same
    state always selects the same list.
L3 (second-demand pin, §4 = `benchmarks/metrics/policies.py` fault-pin):
    a page's FIRST render is its first demand (CompSys-faithful: the model
    read the page when it was served), and every digest-unseen later reference
    of one of its identifier tokens is the next demand — pin on the SECOND
    demand, served or not (``demand_count >= 2`` → ``pinned``, exactly the
    simulator's line). Drop-state is irrelevant: a dropped page re-referenced
    is precisely the design's fault.
L4 (unpin on content change, Pichay §3.5 step 4): the pin binds to a page key
    of (tool identity + content rollup); a NEW rollup for the same identity
    releases the old page's pin. Transcript messages are immutable, so the old
    row is never rewritten — the release changes state only.
L5 (keep law, §4): the system prompt, the head-protected messages (stock keep
    law), the tail-protected messages, the LAST user message, and any message
    containing an OPEN tool call (a call id with no tool reply in the request)
    are ALWAYS in the request list. The keep law wins over the budget: if the
    hard floor alone reaches vBudget the engine leaves the request untouched
    for this round (the bust is the T0 lock error made visible, and pages
    never rescue a busting floor).
L6 (budget arithmetic, §4): the estimate is the apx4-char family answer —
    ``ceil(chars / 4)`` plus a 4-token per-message structural cost — rounded
    UP so an under-count can never overshoot the enforced budget. The
    estimator is engine-owned; the observer plugin tokenizes in its own
    bookkeeping (the two must not be conflated, §4 bullet 3).
L7 (cheap by construction, W4 §3 hook-cost discipline): no network, no
    filesystem writes, no logging, no threads; selection is string/dict work
    at ms scale. ``select_context`` returns None whenever nothing must be
    dropped and nothing must be repositioned, which also keeps that request
    byte-identical and the cache prefix untouched.

vBudget defaults to the preregistered 24,000 (§5). ``CTXVM_VBUDGET`` may
CONFIRM or RAISE it at the T0 lock (a valid env value wins over a
constructor-passed value — the env is the owner's binding surface; the ctor
argument is the test seam). A LOWERING below 24,000 is refused: lowering the
budget tunes the arms toward PASS, which is a prereg deviation the harness
records — never engine behavior. A malformed env value is an ABSENCE (the
preregistered number applies), never a silent zero.
"""

import copy
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

try:  # host ABC, present inside hermes; absent in the plugin's own test suite
    from agent.context_engine import ContextEngine  # type: ignore

    _HOST_ABC = True
except Exception:  # pragma: no cover - exercised only outside the hermes runtime
    ContextEngine = object  # type: ignore[assignment, misc]
    _HOST_ABC = False

_MIN_TOKEN_LEN = 3   # identifier tokens shorter than this are noise
_MSG_OVERHEAD_TOKENS = 4          # role/tool_call_id/wrapper JSON, per message
_PREREGISTERED_VBUDGET = 24_000   # §5; the T0 lock may CONFIRM or RAISE, never lower

# Sentence-final punctuation splits too: prose commonly ends a sentence right
# after an identifier ("open notes/alpha.md."), and a period glued to the token
# would hide the demand (found in the 2026-11-06 pin tests). Version-number
# pieces ("1.2.3") fall apart into sub-length-3 fragments — acceptable: they
# were noise, not page identifiers.
_SPLIT_RE = re.compile(r"[\s\"',:;().?!\[\]{}|]+")

_PRESENT = object  # sentinel namespace kept for clarity in assertions below


def _is_token_count(value: Any) -> bool:
    """node mirror: whole numbers >= 0 only; booleans refused."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _estimate_tokens(text: str) -> int:
    """L6: apx4-char family arithmetic, rounded UP."""
    return (len(text) + 3) // 4


def _message_text(message: Dict[str, Any]) -> str:
    """Every content byte the provider sees, in deterministic order: content
    strings verbatim; content item lists via text items with non-text items as
    type markers; ``tool_calls`` names and argument payloads appended (they ARE
    prompt bytes)."""
    parts: List[str] = []
    content = message.get("content")
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, dict):
                name = item.get("name")
                parts.append("<{0}{1}>".format(
                    item.get("type", "item"),
                    ":" + name if isinstance(name, str) else ""))
    calls = message.get("tool_calls")
    if isinstance(calls, list):
        for call in calls:
            if not isinstance(call, dict):
                continue
            fn = call.get("function") if isinstance(call.get("function"), dict) else {}
            if isinstance(fn.get("name"), str):
                parts.append(fn["name"])
            args = fn.get("arguments")
            if isinstance(args, str):
                parts.append(args)
            elif args is not None:
                parts.append(json.dumps(args, ensure_ascii=False, sort_keys=True))
    if isinstance(message.get("tool_call_id"), str):
        parts.append(str(message["tool_call_id"]))
    return "\n".join(p for p in parts if p)


def _tokens_for(message: Dict[str, Any]) -> int:
    return _MSG_OVERHEAD_TOKENS + _estimate_tokens(_message_text(message))


def _demand_text(message: Dict[str, Any]) -> str:
    """The demand surface (L3): the side of the conversation the MODEL and the
    USER author — the current request's prose and the assistant's tool-call
    argument payloads (a re-invocation of the same reference IS a demand,
    exactly the simulator's reference string). Provider-authored bodies are
    deliberately NOT a demand surface (a tool result demanding another page's
    path would let the harness write infer demand; identifier_scan stays
    inference, never gate-grade per the W3 law), and the system prompt is
    static plumbing, never a NEW request's reference. Tool-result bodies
    cannot demand their own page either: a page is never credited on a message
    that carries it (the birth-index rule in _credit_demand)."""
    role = message.get("role")
    if role in ("tool", "system"):
        return ""
    parts: List[str] = []
    content = message.get("content")
    if isinstance(content, str):
        parts.append(content)
    elif isinstance(content, list):
        parts.extend(str(item.get("text", "")) for item in content
                     if isinstance(item, dict) and item.get("type") == "text")
    calls = message.get("tool_calls")
    if isinstance(calls, list):
        for call in calls:
            if not isinstance(call, dict):
                continue
            fn = call.get("function") if isinstance(call.get("function"), dict) else {}
            args = fn.get("arguments")
            if isinstance(args, str):
                parts.append(args)
            elif args is not None:
                parts.append(json.dumps(args, ensure_ascii=False, sort_keys=True))
    return "\n".join(p for p in parts if p)


def _value_tokens(args: Any) -> Set[str]:
    """Just the identifier-bearing bytes of a tool call's arguments: the
    VALUES (recursively), never the parameter keys. A generic key like
    ``path`` is plumbing shared by every call to the tool — as a demand token
    it would cross-fire one page from another (read_file(path=alpha) would
    demand read_file(path=br)). Undecidable shapes unwrap to the raw text."""
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = args
    if isinstance(args, dict):
        chunks: List[str] = []
        stack: List[Any] = list(args.values())
        while stack:
            v = stack.pop()
            if isinstance(v, dict):
                stack.extend(v.values())
            elif isinstance(v, (list, tuple)):
                stack.extend(v)
            elif isinstance(v, str):
                chunks.append(v)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                chunks.append(str(v))
        args_text = "\n".join(chunks)
    elif isinstance(args, (list, tuple)):
        flat: List[str] = []
        stack: List[Any] = list(args)  # type: ignore[assignment]
        while stack:
            v = stack.pop()
            if isinstance(v, dict):
                stack.extend(v.values())
            elif isinstance(v, (list, tuple)):
                stack.extend(v)
            elif isinstance(v, str):
                flat.append(v)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                flat.append(str(v))
        args_text = "\n".join(flat)
    else:
        args_text = args if isinstance(args, str) else ""
    return {t for t in _SPLIT_RE.split(args_text)
            if len(t) >= _MIN_TOKEN_LEN and not t.startswith("_truncated")}


def _identity_of_call(call: Dict[str, Any]) -> Tuple[str, FrozenSet[str], str]:
    """Tool identity for a call: (name, argument-value tokens, text).

    The identifier surface the model can re-mention is the invocation's
    argument VALUES (the file path, the command, the query); the tool name and
    the parameter keys do not demand. An unreadable argument payload
    contributes nothing — the page then pins only via re-rolls, never via
    prose."""
    fn = call.get("function") if isinstance(call.get("function"), dict) else {}
    name = fn["name"] if isinstance(fn.get("name"), str) else "unknown"
    args = fn.get("arguments")
    return name, frozenset(sorted(_value_tokens(args))), (
        args if isinstance(args, str) else "")


def _rollup(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8", "surrogatepass")).hexdigest()[:16]


# Activation record (2026-11-07, RR-W8ARM2): the engine object is CONSTRUCTED
# unconditionally at plugin load, so "a ctxvm engine was built" is true in every process and
# says nothing about which arm ran. What the experiment needs is whether the host ever
# ACTIVATED this engine — i.e. whether select_context() was called at all. That is a
# behavioural fact of the process, so it is only meaningful when one gateway serves one
# arm (design/w8-run-plan.md 4c); a multiplexer serving both arms cannot attest either one.
ACTIVATIONS = {"select": 0, "firstTs": None, "lastTs": None}
# Module-global entry counter: a measurement read through another object has misled this card three
# times; this one cannot be out of step with the code path that ran.
ENTERED = {"n": 0}
# Module-global observer slot. Per-session callbacks have now been lost to instance identity three
# times (clone at build, second registration, sidecar reading another object); a module global cannot
# be out of step with the code that fires it.
OBSERVER: Dict[str, Any] = {"cb": None}
# Per-selection request sizes, module-global for the same reason as the observer: the capture must be
# able to read what the engine did without depending on which instance or which state dict it finds.
CALL_LOG: List[Dict[str, int]] = []


class _PageUnit:
    """One tool-call → tool-result page in the CURRENT request (pairing is
    1:1 by ``tool_call_id``)."""

    __slots__ = ("key", "identity", "id_toks", "tokens",
                 "result_index", "call_index", "call_id")

    def __init__(self, key: str, identity: str, id_toks: FrozenSet[str], tokens: int,
                 result_index: int, call_index: int, call_id: str):
        self.key = key
        self.identity = identity     # tool name + argument values (the L4 track)
        self.id_toks = id_toks       # the page's identifier tokens (the L3 surface)
        self.tokens = tokens         # L6 estimate of the tool message's bytes
        self.result_index = result_index
        self.call_index = call_index
        self.call_id = call_id


class CtxvmFaultPinEngine(ContextEngine):  # type: ignore[misc, valid-type]
    """The paged arm's engine (§3/§4). Registered under the name ``"ctxvm"``;
    the host activates it only when a profile carries ``context.engine:
    "ctxvm"``. Class identity is defined unconditionally so the plugin's own
    test suite can stub the host ABC; inside hermes it is a real
    ``agent.context_engine.ContextEngine``."""

    emit_automatic_compaction_status = False

    def __init__(self, v_budget: Optional[int] = None,
                 protect_first_n: int = 3, protect_last_n: int = 6):
        super().__init__()
        self._v_budget, self._v_budget_source, self._v_budget_refused_lower = \
            _resolve_v_budget(v_budget)
        self._v_budget_explicit = v_budget is not None
        # Selection count ON THE INSTANCE, not in a module global. The plugin package is
        # namespaced per profile (hermes_cli/plugins_loader.py `_directory_module_name`
        # gives the first scope `hermes_plugins.<slug>` and every other scope a
        # `__home_<digest>` suffix), but this sibling module is imported flat, and a flat
        # import resolves through sys.modules by bare name. An instance attribute cannot be
        # shared between profiles, whatever the import machinery does.
        # A MUTABLE meter, shared with every clone. The host deep-copies the engine per
        # agent (`clone_for_agent()` defaults to deepcopy, agent_init.py:1828-1841), so an
        # int attribute is copied and the clone's increments never reach the instance the
        # plugin holds. Measured 2026-11-09: a 14-read paged cell reported
        # `engineSelections: 0` while the host log showed no fallback, i.e. the engine was
        # running and the witness was reading the wrong object.
        # Per PROFILE, because one gateway serves every arm from one engine object: a flat
        # process counter made a control sidecar report the probes that ran on the treatment
        # (measured 2026-11-11: naive sidecar read 2 selections it never made).
        self._meter: Dict[str, Any] = {"select": 0, "entered": 0, "skipped_control": 0,
                                      "by_profile": {}}
        # W8C step 2: the observer that turns a selection into trace facts. Set by the plugin per
        # session, because one engine serves every arm and the callback must land in the right tracer.
        # Held in a one-slot list so a per-agent CLONE shares it: the host deepcopies the engine
        # at agent build (before any turn), and a copied None would blind the clone forever while the
        # plugin kept setting the observer on the process-level original (measured 2026-11-12).
        self._observer_ref: List[Any] = [None]
        self._last_policy: Optional[Dict[str, Any]] = None
        self._selections = 0
        # stock keep-law defaults (the host ABC's own class-level values)
        self._protect_first_n = int(protect_first_n)
        self._protect_last_n = int(protect_last_n)
        self._reset_page_state()

    # ---- lifecycle ------------------------------------------------------------

    def _reset_page_state(self) -> None:
        # page key → {"tokens", "pinned", "demand_count", "id_toks", "birth"}
        self._pages: Dict[str, Dict[str, Any]] = {}
        self._pin_order: List[str] = []             # L1(c): frozen first-pin order
        self._identity_active: Dict[str, str] = {}  # identity name → newest key (L4)
        self._credited_texts: Set[str] = set()      # demand digests (L3 dedup)
        self._sighted: Set[str] = set()             # KEY@result_index re-render dedup

    @property
    def name(self) -> str:
        return "ctxvm"

    # ---- abstract contract: the budget lives in selection ---------------------

    def should_compress(self, prompt_tokens: Optional[int] = None) -> bool:
        return False  # never compacts; the budget is enforced by selection

    def compress(self, messages: List[Dict[str, Any]], current_tokens: Optional[int] = None,
                 focus_topic: Optional[str] = None, force: bool = False,
                 memory_context: str = "") -> List[Dict[str, Any]]:
        return messages  # contract-satisfying no-op (§3 item 2)

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        """Token-state bookkeeping the host reads directly (run_agent.py). The
        engine's own budget arithmetic never consumes these numbers (L6 keeps
        the estimate engine-owned), but the ABC requires maintainers, and the
        host status page does."""
        if not isinstance(usage, dict):
            return
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
        total = usage.get("total_tokens")
        if _is_token_count(prompt):
            self.last_prompt_tokens = prompt
        if _is_token_count(completion):
            self.last_completion_tokens = completion
        if _is_token_count(total):
            self.last_total_tokens = total

    def prune_tool_results_only(self, messages: List[Dict[str, Any]],
                                current_tokens: Optional[int] = None,
                               ) -> Tuple[List[Dict[str, Any]], int]:
        return messages, 0  # preregistered no-op (§4): all selection lives here

    # ---- the selection seam (§3.3) ---------------------------------------------

    def select_context(
        self,
        request_messages: List[Dict[str, Any]],
        *,
        conversation_messages: Optional[List[Dict[str, Any]]] = None,
        incoming_message: Optional[Dict[str, Any]] = None,
        budget_tokens: int = 0,
    ) -> Optional[List[Dict[str, Any]]]:
        """Per-request resident-set replacement (§3.3 item 2). Returns None to
        leave the request byte-identical; the returned list is request-only."""
        # Entry counter: "called but selected nothing" must be distinguishable from "never called"
        try:
            self._meter["entered"] += 1
        except Exception:
            pass
        try:
            ENTERED["n"] += 1
        except Exception:
            pass
        # Unconditional file trace of the call itself. The meter is shared with the host's clone, but
        # a shared dict read through another object is exactly the kind of evidence that has misled
        # this card twice; an append-only line is not (0.13.7).
        try:
            import os as _os, time as _time
            _d = Path(_os.environ.get("CTXVM_TRACE_DIR") or
                      (Path(_os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
                       / "ctxvm" / "traces"))
            _d.mkdir(parents=True, exist_ok=True)
            with open(_d / "_entered.log", "a", encoding="utf-8") as _f:
                _f.write(f"{_time.strftime('%Y-%m-%dT%H:%M:%S')} select_context "
                         f"messages={len(request_messages)} entered={self._meter.get('entered')}\n")
        except Exception:
            pass
        # ---- which arm is this turn? (per SESSION, not per process) --------------
        # One gateway holds one plugin instance, so at registration the settings snapshot was the
        # paged profile's and was applied to every session: measured 2026-11-11, the naive arm
        # reported `engine: ctxvm` and `70000/settings`. The profile is knowable here because the
        # host scopes a turn with a contextvar that reaches this worker (gateway/run.py
        # _profile_runtime_scope -> set_hermes_home_override -> get_hermes_home()).
        pol = None
        try:
            from profile_policy import policy as _policy_for_turn  # live sibling, flat import
            pol = _policy_for_turn()
        except Exception:  # noqa: BLE001 - outside the host: treat as control, never as treatment
            pol = None
        self._last_policy = pol
        if pol is not None:
            _prof = pol.get("profile") or "?"
            _bucket = self._meter.setdefault("by_profile", {}).setdefault(
                _prof, {"select": 0, "skip": 0})
            if pol.get("engine") != "ctxvm":
                # Control arm: the host may have activated this engine for the process, but the
                # profile this session belongs to says compressor. Leave the request untouched.
                self._meter["skipped_control"] = self._meter.get("skipped_control", 0) + 1
                _bucket["skip"] += 1
                try:
                    import os as _os
                    _d = Path(_os.environ.get("CTXVM_TRACE_DIR") or
                              (Path(_os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
                               / "ctxvm" / "traces"))
                    _d.mkdir(parents=True, exist_ok=True)
                    with open(_d / "_decision.log", "a", encoding="utf-8") as _f:
                        _f.write(f"{_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')} "
                                 f"RETURNED-CONTROL arm={pol.get('arm')} engine={pol.get('engine')!r} "
                                 f"home={pol.get('home')!r} session_profile={pol.get('profile')!r}\n")
                except Exception:
                    pass
                return None
            # A budget given to the constructor is the caller's decision (the test suite uses tiny
            # ones to exercise the laws), and a policy whose home does not exist is not a session
            # (the suite patches one to keep the laws runnable). Only a real, unset session adopts.
            _home = pol.get("home") or ""
            _real_home = bool(_home) and __import__("os").path.isdir(_home)
            if (not self._v_budget_explicit and _real_home and isinstance(pol.get("budget"), int)
                    and pol["budget"] != self._v_budget):
                self._v_budget = pol["budget"]
                self._v_budget_source = pol.get("budgetSource", self._v_budget_source)

        import datetime as _dt
        self._selections += 1
        self._meter["select"] += 1
        ACTIVATIONS["select"] += 1
        if pol is not None:
            self._meter["by_profile"][pol.get("profile") or "?"]["select"] += 1
        _now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        ACTIVATIONS["firstTs"] = ACTIVATIONS["firstTs"] or _now
        ACTIVATIONS["lastTs"] = _now

        units = self._classify(request_messages)
        self._update_page_state(units)
        self._credit_demand(request_messages)

        keep_hard = self._hard_keep(request_messages, units)
        dropped, repositioned = self._plan(request_messages, units, keep_hard)
        try:
            # The decision, recorded where it is made: the live counters said "entered 57, selected 0"
            # and could not say whether the plan found nothing or the call never got that far.
            import os as _os
            _d = Path(_os.environ.get("CTXVM_TRACE_DIR") or
                      (Path(_os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
                       / "ctxvm" / "traces"))
            _d.mkdir(parents=True, exist_ok=True)
            with open(_d / "_decision.log", "a", encoding="utf-8") as _f:
                _f.write(f"{_dt.datetime.now(_dt.timezone.utc).isoformat(timespec='seconds')} "
                         f"arm={(pol or {}).get('arm')} engine={(pol or {}).get('engine')!r} "
                         f"home={(pol or {}).get('home')!r} budget={self._v_budget} "
                         f"units={len(units)} kept={len(keep_hard)} dropped={len(dropped)} "
                         f"repositioned={len(repositioned)} "
                         f"resident={sum(u.tokens for u in units.values()) if isinstance(units, dict) else 0}\n")
        except Exception:
            pass
        if not dropped and not repositioned:
            return None  # L7: nothing changed → byte-identical request
        assembled = self._assemble(request_messages, units, keep_hard, dropped, repositioned)
        try:
            CALL_LOG.append({"before": sum(_tokens_for(m) for m in request_messages),
                             "after": sum(_tokens_for(m) for m in assembled)})
            del CALL_LOG[:-200]
        except Exception:
            pass
        # W8C: tell the observer what this selection cost. Until 2026-11-11 the engine rewrote the
        # request and said nothing, so the trace reported evictedTokens 0 on a session whose
        # residency was capped at the budget — a real treatment that no capture could witness.
        try:
            evicted = sum(units[i].tokens for i in dropped if i in units)
            if OBSERVER["cb"] is not None and (dropped or repositioned):
                OBSERVER["cb"]({
                    "evictedTokens": evicted,
                    "dropped": [sorted(units[i].id_toks) for i in sorted(dropped) if i in units],
                    "repositioned": sorted(repositioned),
                    # Per-CALL sizes, because a turn has two requests and a turn-level series cannot
                    # score the simulator: measured 2026-11-12, the naive model misses the onset by a
                    # turn and the total by 31 %, and both residuals come from that aggregation.
                    "beforeTokens": sum(_tokens_for(m) for m in request_messages),
                    "afterTokens": sum(_tokens_for(m) for m in assembled),
                })
        except Exception:  # noqa: BLE001 - reporting must never break a selection
            pass
        return assembled

    # ---- pass 1: pairing --------------------------------------------------------

    def _classify(self, messages: List[Dict[str, Any]]) -> Dict[int, _PageUnit]:
        """Pair tool results with their producing calls in THIS request:
        result message index → _PageUnit."""
        units: Dict[int, _PageUnit] = {}
        pending: Dict[str, Tuple[int, str, FrozenSet[str]]] = {}
        for i, m in enumerate(messages):
            if not isinstance(m, dict):
                continue
            role = m.get("role")
            if role == "assistant" and isinstance(m.get("tool_calls"), list):
                for call in m["tool_calls"]:
                    if isinstance(call, dict) and isinstance(call.get("id"), str):
                        pending[call["id"]] = (i,) + _identity_of_call(call)[:2]
            elif role == "tool" and isinstance(m.get("tool_call_id"), str):
                opener = pending.pop(m["tool_call_id"], None)
                if opener is None:
                    continue
                call_index, tool_name, arg_toks = opener
                body = m.get("content")
                text = body if isinstance(body, str) else _flat_content_text(m)
                # pages key on the tool identity + the result's content rollup
                key = "{0}#{1}".format(tool_name, _rollup(text)) if text else None
                if key is None:
                    continue  # a bodyless tool reply is not a page
                identity = "{0}[{1}]".format(tool_name, ",".join(sorted(arg_toks)))
                units[i] = _PageUnit(key, identity, arg_toks, _tokens_for(m),
                                     i, call_index, m["tool_call_id"])
        return units

    # ---- pass 2: page table -----------------------------------------------------

    def _update_page_state(self, units: Dict[int, _PageUnit]) -> None:
        """Register/refresh this request's pages in the persistent table.

        - Creation: the page's first render is demand 1 (L3 — the model read
          the page when it was served).
        - Re-sight: the same key arriving on a NEW result message is a later
          render (a re-read) — one more demand, deduped per (key, message
          position) so per-request re-observation cannot double-credit.
        - L4: a new key under a known identity releases the identity's old
          pin."""
        for u in sorted(units.values(), key=lambda x: x.result_index):
            stamp = "{0}@{1}".format(u.key, u.result_index)
            page = self._pages.get(u.key)
            if page is None:
                self._pages[u.key] = {
                    "tokens": u.tokens, "pinned": False, "demand_count": 1,
                    "id_toks": u.id_toks, "birth": u.result_index,
                }
                self._sighted.add(stamp)
            else:
                if not page["id_toks"] and u.id_toks:
                    page["id_toks"] = u.id_toks  # first sighting's arg tokens stand
                page["tokens"] = max(page["tokens"], u.tokens)
                if stamp not in self._sighted:
                    self._sighted.add(stamp)
                    page["demand_count"] += 1  # a re-render is a demand
                    if page["demand_count"] >= 2:
                        self._ensure_pinned(u.key)
            # L4: a new key under a known identity releases the identity's old pin.
            active = self._identity_active.get(u.identity)
            if active is not None and active != u.key:
                self._release_pin(active)   # L4: new rollup releases the old pin
                self._identity_active[u.identity] = u.key
            else:
                self._identity_active.setdefault(u.identity, u.key)

    def _credit_demand(self, messages: List[Dict[str, Any]]) -> None:
        """W8C: prose is NOT a demand. Mentions are counted as telemetry only.

        Until 2026-11-11 this method pinned a page when any new message text named one of its
        argument values. On a read-once task that pinned 19 of 21 pages, because the model's own
        reply ("part-01.txt is 16,602 bytes") and the final artefact prompt both name the files —
        and a pinned page is protected, so the budget could never bite. Measured twice: 0 evictions
        at 70,000 and 90,000 with 43 selections.

        A demand is now a MODEL-INITIATED RE-READ: a second tool call for the same arguments, seen by
        `note_refault()` at call time, or the same page key arriving on a new result message in
        `_update_page_state` (the re-render path, unchanged). Prose mentioning a page proves nothing
        about whether the model needs it: the harness re-sends the same text on every request.
        """
        for i, m in enumerate(messages):
            if not isinstance(m, dict):
                continue
            text = _demand_text(m)
            if not text:
                continue
            digest = hashlib.sha256(text.encode("utf-8", "surrogatepass")).hexdigest()
            if digest in self._credited_texts:
                continue
            self._credited_texts.add(digest)
            words = {w for w in _SPLIT_RE.split(text) if len(w) >= _MIN_TOKEN_LEN}
            for key, page in self._pages.items():
                if page["birth"] >= i:
                    continue  # the birth rule still decides what could be demanded
                toks = page["id_toks"]
                if toks and not toks.isdisjoint(words):
                    page["prose_mentions"] = page.get("prose_mentions", 0) + 1  # telemetry, never a pin

    def set_observer(self, callback: Any) -> None:
        """Install the per-session observer the plugin uses to record selections (W8C)."""
        self._observer_ref[0] = callback
        OBSERVER["cb"] = callback

    def note_refault(self, args: Any) -> int:
        """W8C: the model asked for the same page again — pin it, at CALL time.

        `args` is the tool call's argument payload as the host delivers it (a JSON string or a dict);
        it is tokenised with the same rule the page table uses, so the identity cannot drift between
        the observer and the engine. Returns the number of pages newly pinned.
        """
        try:
            toks = frozenset(sorted(_value_tokens(args)))
        except Exception:  # noqa: BLE001 - an unreadable payload demands nothing
            return 0
        if not toks:
            return 0
        pinned = 0
        for key, page in self._pages.items():
            if toks.isdisjoint(page["id_toks"]):
                continue
            page["demand_count"] = page.get("demand_count", 1) + 1
            page["refaults"] = page.get("refaults", 0) + 1
            if page["demand_count"] >= 2 and not page["pinned"]:
                self._ensure_pinned(key)
                pinned += 1
        return pinned

    # ---- pass 3: keeps, budget, drops --------------------------------------------

    def _hard_keep(self, messages: List[Dict[str, Any]],
                   units: Dict[int, _PageUnit]) -> Set[int]:
        """L5: system, head-protected, tail-protected, last user, open calls."""
        keep: Set[int] = set()
        for i, m in enumerate(messages):
            if isinstance(m, dict) and m.get("role") == "system":
                keep.add(i)
        non_system = [i for i, m in enumerate(messages)
                      if isinstance(m, dict) and m.get("role") != "system"]
        if self._protect_first_n:
            keep.update(non_system[: self._protect_first_n])
        if self._protect_last_n:
            keep.update(non_system[-self._protect_last_n :])
        answered = {u.call_id for u in units.values()}
        last_user: Optional[int] = None
        for i, m in enumerate(messages):
            if not isinstance(m, dict):
                continue
            if m.get("role") == "user":
                last_user = i
            calls = m.get("tool_calls") if m.get("role") == "assistant" else None
            if isinstance(calls, list) and any(
                    isinstance(c, dict) and isinstance(c.get("id"), str)
                    and c["id"] not in answered for c in calls):
                keep.add(i)  # an OPEN tool call never drops (L5)
        if last_user is not None:
            keep.add(last_user)
        return keep

    def _plan(self, messages: List[Dict[str, Any]], units: Dict[int, _PageUnit],
              keep_hard: Set[int]) -> Tuple[Set[int], Set[str]]:
        """The budget decision. Returns (dropped result indices, repositioned
        page keys). The invariant both outputs inherit: hard keeps never drop,
        pinned pages never drop, and pinned pages reposition into the L1(c)
        block. Pin-crunch (pinned + floor + scaffold already above
        vBudget): nothing else can come out — the non-pinned pages all drop,
        which is the smallest achievable request that still honors L5."""
        floor_tokens = sum(_tokens_for(messages[i]) for i in keep_hard)
        if floor_tokens >= self._v_budget:
            return set(), set()  # L5: keep law owns this request; pages never rescue
        scaffold_tokens = sum(_tokens_for(messages[i]) for i in range(len(messages))
                              if i not in keep_hard and i not in units)
        present_keys = {u.key for u in units.values()}
        pinned_keys = [k for k in self._pin_order if k in present_keys]
        pinned_set = set(pinned_keys)
        pinned_tokens = sum(self._pages[k]["tokens"] for k in pinned_keys)
        remain = self._v_budget - floor_tokens - scaffold_tokens - pinned_tokens

        # the newest unpinned, non-hard pages fill what remains; the walk stops
        # at the first page that does not fit and everything older drops with
        # it — kept pages stay a contiguous recency window, append-stable (L1d)
        dropped: Set[int] = set()
        kept_run = 0
        walk = sorted((u for i, u in units.items()
                       if i not in keep_hard and u.key not in pinned_set),
                      key=lambda u: -u.result_index)
        for idx, u in enumerate(walk):
            t = self._pages[u.key]["tokens"]
            if kept_run + t <= remain:
                kept_run += t
            else:
                dropped = {x.result_index for x in walk[idx :]}
                break
        return dropped, set(pinned_keys)

    # ---- pass 4: assembly ---------------------------------------------------------

    def _assemble(self, messages: List[Dict[str, Any]], units: Dict[int, _PageUnit],
                  keep_hard: Set[int], dropped: Set[int],
                  repositioned: Set[str]) -> List[Dict[str, Any]]:
        """L1 ordering with pair-validity by rewrite-on-copy (originals are
        never mutated): the block carries a reduced single-call copy of the
        producing assistant message plus the result verbatim; every transcript
        position of a block member is rewritten out; dropped pairs vanish
        together."""
        dropped_keys = {units[i].key for i in dropped}
        by_key: Dict[str, _PageUnit] = {}
        for u in units.values():
            by_key.setdefault(u.key, u)
        repositioned_results = {by_key[k].result_index for k in repositioned if k in by_key}
        repositioned_calls = {by_key[k].call_id for k in repositioned if k in by_key}
        removed_results = dropped | repositioned_results
        removed_ids = {units[i].call_id for i in dropped} | repositioned_calls

        out: List[Dict[str, Any]] = []
        # (a) system prompt verbatim, first
        for i, m in enumerate(messages):
            if isinstance(m, dict) and m.get("role") == "system":
                out.append(m)
        # (b) head-protected non-system messages (stock keep law), transcript order
        non_system = [i for i, m in enumerate(messages)
                      if isinstance(m, dict) and m.get("role") != "system"]
        for i in non_system[: self._protect_first_n]:
            self._emit_transcript_slot(out, messages, units, i, removed_ids, removed_results)
        # (c) the pinned block, frozen first-pin order
        for key in self._pin_order:
            if key not in repositioned:
                continue
            u = by_key[key]
            out.append(self._single_call_copy(messages[u.call_index], u.call_id))
            out.append(messages[u.result_index])  # verbatim: the page body
        # (d) everything else kept, transcript order (the recency tail)
        head = set(non_system[: self._protect_first_n])
        for i, m in enumerate(messages):
            if i in head or (isinstance(m, dict) and m.get("role") == "system"):
                continue  # already emitted
            self._emit_transcript_slot(out, messages, units, i, removed_ids, removed_results)
        return out

    def _emit_transcript_slot(self, out: List[Dict[str, Any]], messages: List[Dict[str, Any]],
                              units: Dict[int, _PageUnit], i: int,
                              removed_ids: Set[str], removed_results: Set[int]) -> None:
        """Emit one transcript position under the drop/rewrite rules, or skip
        it: dropped results go; repositioned results go (they ride the block);
        assistant carriers lose their removed call entries in a COPY and are
        dropped entirely when nothing visible remains."""
        m = messages[i]
        if not isinstance(m, dict):
            out.append(m)
            return
        u = units.get(i)
        if u is not None and m.get("role") == "tool":
            if i in removed_results:
                return  # the page body rides the block (repositioned) or is dropped
            out.append(m)
            return
        calls = m.get("tool_calls")
        if isinstance(calls, list) and any(
                isinstance(c, dict) and c.get("id") in removed_ids for c in calls):
            kept_calls = [c for c in calls
                          if isinstance(c, dict) and c.get("id") not in removed_ids]
            has_content = bool(m.get("content"))
            if kept_calls or has_content:
                reduced = copy.deepcopy(m)
                reduced["tool_calls"] = kept_calls
                out.append(reduced)
                return
            return  # the carrier held only dropped calls → nothing to transmit
        out.append(m)

    @staticmethod
    def _single_call_copy(message: Dict[str, Any], call_id: str) -> Dict[str, Any]:
        """A fresh reduced carrier: the one call this block entry binds,
        original content preserved (the model may narrate around calls)."""
        copy_m = copy.deepcopy(message)
        copy_m["tool_calls"] = [c for c in copy_m.get("tool_calls", [])
                                if isinstance(c, dict) and c.get("id") == call_id]
        # keep only the truthy provider fields a single-call carrier needs
        return copy_m

    # ---- pin helpers ------------------------------------------------------------

    def _ensure_pinned(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None or page["pinned"]:
            return
        page["pinned"] = True
        if key not in self._pin_order:      # L1(c): append after the block
            self._pin_order.append(key)

    def _release_pin(self, key: str) -> None:
        page = self._pages.get(key)
        if page is not None:
            page["pinned"] = False
        while key in self._pin_order:       # the ORDER of the remaining pins stays
            self._pin_order.remove(key)

    # ---- informational state ----------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        status = super().get_status()
        status.update({
            "engine": self.name,
            "vBudget": self._v_budget,
            "vBudgetSource": self._v_budget_source,
            "vBudgetRefusedLower": self._v_budget_refused_lower,
            "pages": len(self._pages),
            "pinned": len(self._pin_order),
        })
        return status

    def on_session_reset(self) -> None:
        """/new or /reset: the page table is per-session state (§4)."""
        super().on_session_reset()
        self._reset_page_state()

    # ---- copying (§3.3 item 2: plain dicts of ints/strings — deepcopy is right) --

    def __deepcopy__(self, memo: Dict[int, Any]) -> "CtxvmFaultPinEngine":
        fresh = CtxvmFaultPinEngine.__new__(CtxvmFaultPinEngine)
        memo[id(self)] = fresh
        fresh.__dict__.update(copy.deepcopy(self.__dict__, memo))
        # The meter is the one attribute a clone must SHARE, not copy: the plugin holds the
        # original, the host runs the clone, and the selection count has to be visible to both.
        fresh._meter = self._meter
        fresh._observer_ref = self._observer_ref
        return fresh


def _flat_content_text(message: Dict[str, Any]) -> str:
    """The result body of a tool message whose content is a list: text items
    joined; non-text items as type markers (the observer's pageBody rule)."""
    content = message.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, dict):
                return ""  # mixed non-text bodies key nothing honest; not a page
        return "\n".join(parts)
    return ""


def _resolve_v_budget(ctor_value: Optional[int]) -> Tuple[int, str, bool]:
    """vBudget resolution (§5): preregistered 24,000 unless CTXVM_VBUDGET
    confirms or raises (the env is the owner's T0 binding surface and wins over
    the ctor test seam); a lowering is refused (clamped back, flagged); a
    malformed or non-positive value is an absence (the preregistered number
    applies), never a zero."""
    source = "preregistered"
    candidate: Optional[int] = None
    raw = (os.environ.get("CTXVM_VBUDGET") or "").strip()
    if raw:
        try:
            parsed = int(raw)
        except (TypeError, ValueError):
            parsed = 0
        if _is_token_count(parsed) and parsed > 0:
            candidate, source = parsed, "env CTXVM_VBUDGET"
    if candidate is None and _is_token_count(ctor_value or 0) and ctor_value:
        candidate, source = int(ctor_value), "ctor"
    refused = False
    if candidate is not None and candidate < _PREREGISTERED_VBUDGET:
        candidate = _PREREGISTERED_VBUDGET
        refused = True
    return (candidate if candidate is not None else _PREREGISTERED_VBUDGET), source, refused


def build_engine(v_budget: Optional[int] = None,
                 protect_first_n: int = 3, protect_last_n: int = 6) -> Optional[Any]:
    """Registration-time factory. Returns None outside the hermes runtime (the
    plugin's observer duties never depend on the engine — the registration in
    live/__init__.py is fail-open)."""
    if not _HOST_ABC:
        return None
    return CtxvmFaultPinEngine(v_budget=v_budget,
                               protect_first_n=protect_first_n,
                               protect_last_n=protect_last_n)
