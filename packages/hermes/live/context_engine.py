"""W8 v1 ``FaultPinPolicy`` context engine — the paged arm's control plane.

Design: ``design/past-experiments/w8-capture-design.md`` §3.3/§4 (preregistered; after the first
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


def _content_hash(body: str) -> str:
    """Exact tracer-compatible PageId content hash (sha256:<8 hex>)."""
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:8]


# Activation record (2026-11-07, RR-W8ARM2): the engine object is CONSTRUCTED
# unconditionally at plugin load, so "a ctxvm engine was built" is true in every process and
# says nothing about which arm ran. What the experiment needs is whether the host ever
# ACTIVATED this engine — i.e. whether select_context() was called at all. That is a
# behavioural fact of the process, so it is only meaningful when one gateway serves one
# arm (design/past-experiments/w8-run-plan.md 4c); a multiplexer serving both arms cannot attest either one.
# ROOT CAUSE, measured 2026-11-18: the engine imported its sibling as `from profile_policy import
# policy`. A bare name resolves through sys.modules/sys.path, and the gateway serves every profile, so a
# STALE profile-local plugin copy (`~/.hermes/profiles/w8cp-*/plugins/ctxvm-tracer`, 0.13.23, no
# `selectionMode` in its scanner) won the import. The engine then read a policy dict without the mode and
# H11 never engaged, while the file next to it said `stable`. Load the sibling BY PATH instead: identity
# is then a property of this file's directory, not of whatever a profile put on sys.path.
_POLICY_MOD: Any = None


def _policy_module() -> Any:
    global _POLICY_MOD
    if _POLICY_MOD is None:
        import importlib.util as _iu
        _path = Path(__file__).resolve().parent / "profile_policy.py"
        _spec = _iu.spec_from_file_location("ctxvm_profile_policy", _path)
        _mod = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)          # type: ignore[union-attr]
        _POLICY_MOD = _mod
    return _POLICY_MOD


ACTIVATIONS = {"select": 0, "firstTs": None, "lastTs": None}
# Module-global entry counter: a measurement read through another object has misled this card three
# times; this one cannot be out of step with the code path that ran.
ENTERED = {"n": 0}
# Module-global observer slot. Per-session callbacks have now been lost to instance identity three
# times (clone at build, second registration, sidecar reading another object); a module global cannot
# be out of step with the code that fires it.
OBSERVER: Dict[str, Any] = {"cb": None, "plan": None}
# Two channels on purpose. `cb` reports EVICTIONS and stays silent on a no-op (L7, pinned by a test);
# `plan` reports the budget DECISION on every selection, including the two no-change reasons, because
# "the plan found nothing" and "the engine was never asked" are different facts (H9).
# Per-selection request sizes, module-global for the same reason as the observer: the capture must be
# able to read what the engine did without depending on which instance or which state dict it finds.
CALL_LOG: List[Dict[str, int]] = []


# Part C fix: read-only tools may carry a capped argument excerpt in a stub;
# every other tool (the MUTATING fail-safe class) names the call above instead.
_STUB_READ_ONLY_TOOLS = frozenset({"read_file", "search_files"})
_STUB_ARG_LIMIT = 200


def _stub_arg_excerpt(raw: Any) -> str:
    """Bounded, frame-safe argument text for a recoverable stub. Strips control
    characters/newlines, escapes the `[`/`]` frame, caps length with a marker."""
    s = raw if isinstance(raw, str) else json.dumps(raw, default=str)
    s = "".join(ch if ch.isprintable() else " " for ch in s)
    s = s.replace("[", "\\[").replace("]", "\\]")
    if len(s) > _STUB_ARG_LIMIT:
        s = s[:_STUB_ARG_LIMIT] + "...[truncated]"
    return s


class _PageUnit:
    """One tool-call → tool-result page in the CURRENT request (pairing is
    1:1 by ``tool_call_id``)."""

    __slots__ = ("key", "identity", "id_toks", "tokens",
                 "result_index", "call_index", "call_id", "content_hash")

    def __init__(self, key: str, identity: str, id_toks: FrozenSet[str], tokens: int,
                 result_index: int, call_index: int, call_id: str,
                 content_hash: str):
        self.key = key             # tool name + content rollup
        self.identity = identity   # tool name + argument values (the L4 track)
        self.id_toks = id_toks     # the page's identifier tokens (the L3 surface)
        self.tokens = tokens       # the L6 estimate of the tool message's bytes
        self.result_index = result_index
        self.call_index = call_index
        self.call_id = call_id
        self.content_hash = content_hash  # exact PageId half, never latest-by-ref


class CtxvmFaultPinEngine(ContextEngine):  # type: ignore[misc, valid-type]
    """The paged arm's engine (§3/§4). Registered under the name ``"ctxvm"``;
    the host activates it only when a profile carries ``context.engine:
    "ctxvm"``. Class identity is defined unconditionally so the plugin's own
    test suite can stub the host ABC; inside hermes it is a real
    ``agent.context_engine.ContextEngine``."""

    emit_automatic_compaction_status = False

    def __init__(self, v_budget: Optional[int] = None,
                 protect_first_n: int = 3, protect_last_n: int = 6,
                 selection_mode: Optional[str] = None,
                 stub_dropped: Optional[str] = None,
                 shadow_selection: Optional[bool] = None):
        super().__init__()
        # H11 / design/past-experiments/w8-cache-stable-selection.md. `fresh` is the shipped behaviour: every request
        # is planned from scratch. `stable` HOLDS the selection it last applied, byte-for-byte, until a
        # trigger fires (a page it did not hold appears, the request overflows the budget, or every B-th
        # call). The point is the provider's prefix cache: a selection that rewrites the prefix on every
        # call forfeits it, which is what the W8C pair measured (2.11x dollars).
        self._selection_mode = (selection_mode or os.environ.get("CTXVM_SELECTION_MODE") or "fresh").strip().lower()
        # An EXPLICIT mode (constructor or env) is the caller's decision and is never overridden; a
        # session's own profile setting is adopted at call time, exactly like the budget, because one
        # gateway serves every arm from one engine object.
        self._selection_mode_explicit = bool(selection_mode) or bool(os.environ.get("CTXVM_SELECTION_MODE"))
        # Part C: recoverable stub for DROPPED tool results. Opt-in only — no env
        # fallback, so no ambient shell can turn it on. "off" is the shipped value.
        self._stub_dropped = "off" if stub_dropped is None else str(stub_dropped).strip().lower()
        if self._stub_dropped not in ("off", "recoverable"):
            self._stub_dropped = "off"
        self._stub_explicit = stub_dropped is not None
        # Shadow mode: opt-in profile/constructor only. It records a counterfactual
        # keep-law plan without changing the live request or mutating live page/pin
        # state. No env channel, default off.
        self._shadow_selection = False if shadow_selection is None else bool(shadow_selection)
        self._shadow_explicit = shadow_selection is not None
        try:
            self._stable_every = max(1, int(os.environ.get("CTXVM_SELECTION_EVERY") or 4))
        except (TypeError, ValueError):
            self._stable_every = 4
        self._held: Optional[Dict[str, Any]] = None     # {dropped, repositioned, keys, hash}
        self._calls_since_plan = 0
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

    def _emit_shadow_plan(self, messages: List[Dict[str, Any]], pol: Dict[str, Any],
                          applied: bool) -> None:
        """Counterfactual keep-law plan for a CONTROL session. Uses a fresh
        short-lived engine: no live page/pin mutation, no request change. The
        observer receives a shadow payload; the live return stays None."""
        try:
            budget = pol.get("budget") if isinstance(pol.get("budget"), int) else self._v_budget
            shadow = CtxvmFaultPinEngine(
                v_budget=budget, protect_first_n=self._protect_first_n,
                protect_last_n=self._protect_last_n, selection_mode="fresh",
                stub_dropped="off", shadow_selection=False)
            units = shadow._classify(messages)
            # Replay the SAME page-state and demand passes as the live engine,
            # on the short-lived clone only. This reproduces second-demand
            # pinning, identity release and reposition state for control profiles.
            shadow._update_page_state(units)
            shadow._credit_demand(messages)
            by_key = {u.key: u for u in units.values()}
            keep_hard = shadow._hard_keep(messages, units)
            dropped, repositioned, facts = shadow._plan(messages, units, keep_hard)
            shadow._assemble(messages, units, keep_hard, dropped, repositioned)
            changed = set(dropped)
            for u in units.values():
                if u.key in repositioned:
                    changed.add(u.result_index)
            cut = min(changed) if changed else len(messages)
            digest = hashlib.sha256(json.dumps(
                messages[:min(cut, 8)], sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]
            payload = dict(
                facts, shadow=True, shadowSelection=True, policyApplied=applied,
                requestUnchanged=True,
                dropped=[sorted(units[i].id_toks) for i in sorted(dropped) if i in units],
                droppedPages=[{"ids": sorted(units[i].id_toks), "tokens": units[i].tokens,
                               "contentHash": units[i].content_hash}
                              for i in sorted(dropped) if i in units],
                repositionedPages=[{"ids": sorted(by_key[k].id_toks),
                                    "tokens": by_key[k].tokens,
                                    "contentHash": by_key[k].content_hash}
                                   for k in sorted(repositioned) if k in by_key],
                budgetTokens=budget, prefixHash="sha256:" + digest,
                selectionMode="fresh", policyMode=(pol or {}).get("selectionMode"),
                policyModeSource=(pol or {}).get("selectionModeSource"), modeExplicit=False,
                selectionHash=shadow._selection_hash(dropped, repositioned, units),
                trigger=None, callIndex=len(CALL_LOG))
            if OBSERVER["plan"] is not None:
                OBSERVER["plan"](payload)
        except Exception:  # noqa: BLE001 - shadow observation must never break a turn
            pass

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
            pol = _policy_module().policy()
        except Exception:  # noqa: BLE001 - outside the host: treat as control, never as treatment
            pol = None
        self._last_policy = pol
        if pol is not None:
            _home = pol.get("home") or ""
            _real_home = bool(_home) and __import__("os").path.isdir(_home)
            # Shadow opt-in is adopted BEFORE the control early-return, so a
            # control profile can be observed without changing its request.
            if not self._shadow_explicit and _real_home:
                self._shadow_selection = bool(pol.get("shadowSelection"))
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
                if self._shadow_selection:
                    self._emit_shadow_plan(request_messages, pol, applied=False)
                return None
            # A budget given to the constructor is the caller's decision (the test suite uses tiny
            # ones to exercise the laws), and a policy whose home does not exist is not a session
            # (the suite patches one to keep the laws runnable). Only a real, unset session adopts.
            if (not self._v_budget_explicit and _real_home and isinstance(pol.get("budget"), int)
                    and pol["budget"] != self._v_budget):
                self._v_budget = pol["budget"]
                self._v_budget_source = pol.get("budgetSource", self._v_budget_source)
            # H11: the mode is per SESSION too. A profile that says `stable` decides it for its own
            # turns; a profile that says nothing stays on the shipped `fresh`.
            if not self._selection_mode_explicit and _real_home:
                wanted = pol.get("selectionMode")
                if wanted in ("fresh", "stable") and wanted != self._selection_mode:
                    self._selection_mode = wanted
                    self._held = None            # a mode change starts from a clean hold
                    self._calls_since_plan = 0
            # Part C: adopted at CALL time like the budget/mode (one gateway serves
            # every profile). A profile setting is the only opt-in channel; an
            # explicit constructor value is never overridden.
            if not self._stub_explicit and _real_home:
                wanted_stub = pol.get("stubDropped")
                if wanted_stub in ("off", "recoverable"):
                    self._stub_dropped = wanted_stub

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
        # ---- H11: hold the selection, or plan a new one ------------------------------------
        trigger: Optional[str] = None
        if self._selection_mode == "stable":
            trigger = self._stable_trigger(request_messages, units)
            if trigger is None and self._held is not None:
                dropped = set(self._held["dropped"])
                repositioned = set(self._held["repositioned"])
                resident_tokens = sum(_tokens_for(m) for m in request_messages)
                plan_facts = {
                    "reason": "evicted" if dropped else "fits",
                    "floorTokens": sum(_tokens_for(request_messages[i]) for i in keep_hard),
                    "residentTokens": resident_tokens,
                    "droppedCount": len(dropped),
                    "droppedTokens": sum(units[i].tokens for i in dropped if i in units),
                    "repositionedCount": len(repositioned),
                }
            else:
                dropped, repositioned, plan_facts = self._plan(request_messages, units, keep_hard)
                self._calls_since_plan = 0
                self._held = {
                    "dropped": set(dropped), "repositioned": set(repositioned),
                    "keys": {u.key for u in units.values()},
                    "hash": self._selection_hash(dropped, repositioned, units),
                }
        else:
            dropped, repositioned, plan_facts = self._plan(request_messages, units, keep_hard)
        # page.evict and the request body come from ONE assembly: compute it before
        # the observer so self._stub_rows (exact stub strings) is ready at emit time.
        assembled = self._assemble(request_messages, units, keep_hard, dropped, repositioned)
        # H9: report the DECISION on every selection, including both no-change reasons. The eviction
        # channel below is silent on a no-op by design (L7), so before this block a reader could not
        # separate "the plan found nothing" from "the engine was never asked" — three closed cells
        # were diagnosed with arithmetic that this states in one word.
        try:
            if OBSERVER["plan"] is not None:
                by_key = {u.key: u for u in units.values()}
                _changed = set(dropped)
                for _u in units.values():
                    if _u.key in repositioned:
                        _changed.add(_u.result_index)
                _cut = min(_changed) if _changed else len(request_messages)
                # A fixed probe of the leading protected block, NOT the provider's cache key: it
                # answers "did the head of the request change between calls" (H11's question) and
                # nothing else. Eight messages is the system prompt plus the head-protected window.
                _probe = request_messages[: min(_cut, 8)]
                _digest = hashlib.sha256(
                    json.dumps(_probe, sort_keys=True, default=str).encode("utf-8")
                ).hexdigest()[:16]
                OBSERVER["plan"](dict(plan_facts,
                                      stubDropped=self._stub_dropped,
                                      stubCount=(len(dropped) if self._stub_dropped == "recoverable" else 0),
                                      shadowSelection=self._shadow_selection,
                                      shadow=False,
                                      policyApplied=True,
                                      requestUnchanged=True,
                                      droppedPages=[{"ids": sorted(units[i].id_toks),
                                                     "tokens": units[i].tokens,
                                                     "contentHash": units[i].content_hash}
                                                    for i in sorted(dropped) if i in units],
                                      repositionedPages=[{"ids": sorted(by_key[k].id_toks),
                                                          "tokens": by_key[k].tokens,
                                                          "contentHash": by_key[k].content_hash}
                                                         for k in sorted(repositioned) if k in by_key],
                                      # page.evict rows: exact stub text from the assembly, with the
                                      # producing page's identity tokens for the tracer's refs join.
                                      stubRows=(list(self._stub_rows)
                                                if self._stub_dropped == "recoverable" else []),
                                      budgetTokens=self._v_budget,
                                      prefixHash="sha256:" + _digest,
                                      selectionMode=self._selection_mode,
                                      # Diagnostics for the H11/H12 card: what the policy actually
                                      # said and whether the mode was pinned by the caller. Measured
                                      # 2026-11-18: a live session reported `selectionMode: fresh` with
                                      # `budgetSource: settings`, which is only possible if the policy
                                      # dict lacked the key — these two fields say which it was.
                                      policyMode=((pol or {}).get("selectionMode")),
                                      policyModeSource=((pol or {}).get("selectionModeSource")),
                                      modeExplicit=self._selection_mode_explicit,
                                      selectionHash=self._selection_hash(dropped, repositioned, units),
                                      trigger=(trigger or ("held" if self._selection_mode == "stable"
                                                           else None)),
                                      callIndex=len(CALL_LOG)))
        except Exception:  # noqa: BLE001 - reporting must never break a selection
            pass
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
        # Log EVERY selection, dropping or not: a call log that only holds drops makes the scorer's
        # sign test one-sided (every entry "predicted drop" by construction) — measured 2026-11-12.
        try:
            _before = sum(_tokens_for(m) for m in request_messages)
            if dropped or repositioned:
                _after = sum(_tokens_for(m) for m in
                             assembled)
            else:
                _after = _before
            CALL_LOG.append({
                "i": len(CALL_LOG),
                "before": _before, "after": _after,
                "dropped": len(dropped), "budget": self._v_budget,
                # Per-call identities: which pages THIS call removed, with their own token counts.
                # The wire may take a year to carry this; the sidecar can carry it now.
                "removed": [
                    {"tokens": units[i].tokens, "ids": sorted(units[i].id_toks)[:6]}
                    for i in sorted(dropped) if i in units
                ],
            })
            del CALL_LOG[:-200]
        except Exception:
            pass
        try:
            # One line per selection, with the numbers a reader would otherwise have to infer.
            _dbg_before = sum(_tokens_for(m) for m in request_messages)
            _dbg_after = _dbg_before
            if dropped or repositioned:
                _dbg_after = sum(_tokens_for(m) for m in assembled)
            import os as _os, time as _time
            _d = Path(_os.environ.get("CTXVM_TRACE_DIR") or
                      (Path(_os.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
                       / "ctxvm" / "traces"))
            _d.mkdir(parents=True, exist_ok=True)
            with open(_d / "_selections.log", "a", encoding="utf-8") as _f:
                _f.write(f"{_time.strftime('%Y-%m-%dT%H:%M:%S')} arm={(pol or {}).get('arm')} "
                         f"budget={self._v_budget} before={_dbg_before} after={_dbg_after} "
                         f"dropped={len(dropped)} "
                         f"resident={sum(u.tokens for u in units.values()) if isinstance(units, dict) else 0}\n")
        except Exception as _exc:  # noqa: BLE001 - a log line must never break a selection
            try:
                import os as _os2
                _d2 = Path(_os2.environ.get("CTXVM_TRACE_DIR") or
                           (Path(_os2.environ.get("XDG_STATE_HOME") or (Path.home() / ".local" / "state"))
                            / "ctxvm" / "traces"))
                _d2.mkdir(parents=True, exist_ok=True)
                with open(_d2 / "_swallowed.log", "a", encoding="utf-8") as _f2:
                    _f2.write(f"select_context_log: {type(_exc).__name__}: {_exc}\n")
            except Exception:
                pass
        if not dropped and not repositioned:
            return None  # L7: nothing changed → byte-identical request

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
                    "droppedCount": len(dropped),
                    "callIndex": len(CALL_LOG) - 1,
                    "removed": [
                        {"tokens": units[i].tokens, "ids": sorted(units[i].id_toks)[:6]}
                        for i in sorted(dropped) if i in units
                    ],
                    # Per-CALL sizes, because a turn has two requests and a turn-level series cannot
                    # score the simulator: measured 2026-11-12, the naive model misses the onset by a
                    # turn and the total by 31 %, and both residuals come from that aggregation.
                    "beforeTokens": sum(_tokens_for(m) for m in request_messages),
                    "afterTokens": _after,
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
                                     i, call_index, m["tool_call_id"],
                                     _content_hash(text))
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

    def set_observer(self, callback: Any, plan_callback: Any = None) -> None:
        """Install the per-session observers the plugin uses to record selections (W8C, H9).

        `callback` receives evictions only (L7: an unchanged request reports nothing).
        `plan_callback` receives every selection's plan facts — reason, floor, dropped tokens,
        prefix probe — so a capture can say why a request did or did not change.
        """
        self._observer_ref[0] = callback
        OBSERVER["cb"] = callback
        if plan_callback is not None:
            OBSERVER["plan"] = plan_callback

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

    def _selection_hash(self, dropped: Set[int], repositioned: Set[str],
                        units: Dict[int, _PageUnit]) -> str:
        """Hash the SELECTION, by page identity — not the message bytes.

        design/past-experiments/w8-cache-stable-selection.md asks for volatile markers (timestamps, session ids, cwd,
        counters) to be canonicalised before hashing. Hashing identities instead is stronger and
        cheaper: a page key is `tool#content-rollup`, so no volatile marker can enter the hash at all,
        and the value answers the question the cache actually asks — "would this call send the same
        pages in the same order".
        """
        basis = {
            "dropped": sorted(units[i].key for i in dropped if i in units),
            "repositioned": sorted(repositioned),
        }
        return "sha256:" + hashlib.sha256(
            json.dumps(basis, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    def _stable_trigger(self, messages: List[Dict[str, Any]], units: Dict[int, _PageUnit]) -> Optional[str]:
        """Decide whether a held selection may be reused. Returns the trigger name, or None to hold.

        Three triggers, per the design: a page the held selection did not know about (`new-page`), a
        request that now overflows the budget (`overflow`), and every B-th call (`every-B`).
        """
        self._calls_since_plan += 1
        resident = sum(_tokens_for(m) for m in messages)
        if self._held is not None:
            # A page the held selection never saw is the more informative cause, and it fires first:
            # a 9th page both breaks the held set AND pushes the outgoing size over budget, and
            # reporting "overflow" there names the symptom instead of the reason.
            held_keys = set(self._held["keys"])
            if any(u.key not in held_keys for u in units.values()):
                return "new-page"
            # a held drop whose message is gone can no longer be applied
            if any(i not in units for i in self._held["dropped"]):
                return "new-page"
        # `overflow` must mean the OUTGOING request is over budget, not the incoming one: on the paged
        # arm the incoming request is always above the floor, so a naive `resident > budget` test fired
        # every call and stable mode never held anything.
        outgoing = resident
        if self._held is not None:
            outgoing -= sum(units[i].tokens for i in self._held["dropped"] if i in units)
        if outgoing > self._v_budget:
            return "overflow"
        if self._calls_since_plan >= self._stable_every:
            return "every-B"
        return None

    def _plan(self, messages: List[Dict[str, Any]], units: Dict[int, _PageUnit],
              keep_hard: Set[int]) -> Tuple[Set[int], Set[str], Dict[str, Any]]:
        """The budget decision. Returns (dropped result indices, repositioned
        page keys, plan facts).

        The facts answer "why did this request change, or not" — the question three closed cells
        answered by arithmetic on resident and headroom (H9). ``reason`` is one of:
        ``fits`` (everything the plan could keep fits; pinned pages may still reposition),
        ``floor_bust`` (the keep law's floor alone reaches vBudget, so nothing can be evicted),
        ``evicted`` (the budget bit and at least one page left the request).

        The invariant both outputs inherit: hard keeps never drop,
        pinned pages never drop, and pinned pages reposition into the L1(c)
        block. Pin-crunch (pinned + floor + scaffold already above
        vBudget): nothing else can come out — the non-pinned pages all drop,
        which is the smallest achievable request that still honors L5."""
        floor_tokens = sum(_tokens_for(messages[i]) for i in keep_hard)
        resident_tokens = sum(_tokens_for(m) for m in messages)
        if floor_tokens >= self._v_budget:
            # L5: keep law owns this request; pages never rescue
            return set(), set(), {
                "reason": "floor_bust", "floorTokens": floor_tokens,
                "residentTokens": resident_tokens, "droppedCount": 0,
                "droppedTokens": 0, "repositionedCount": 0,
            }
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
        facts = {
            "reason": "evicted" if dropped else "fits",
            "floorTokens": floor_tokens,
            "residentTokens": resident_tokens,
            "droppedCount": len(dropped),
            "droppedTokens": sum(units[i].tokens for i in dropped if i in units),
            "repositionedCount": len(pinned_keys),
        }
        return dropped, set(pinned_keys), facts

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
        # Part C: when a dropped result is stubbed, its producing call must STAY in
        # the carrier (pair validity) so the model can re-run it. Repositioned pages
        # still ride the block verbatim and are never stubbed.
        stubbed_results = set(dropped) if self._stub_dropped == "recoverable" else set()
        stubbed_calls = {units[i].call_id for i in stubbed_results if i in units}
        removed_ids = ({units[i].call_id for i in dropped} | repositioned_calls) - stubbed_calls

        out: List[Dict[str, Any]] = []
        # Part C/page.evict: the exact stub strings inserted into this request,
        # paired with the producing page's identity tokens. The bridge observer
        # joins ids→refs via refs_for_identity_tokens and emits page.evict with
        # BYTE-IDENTICAL stubText. Never derive event text from the plan.
        self._stub_rows: List[Dict[str, Any]] = []
        # (a) system prompt verbatim, first
        for i, m in enumerate(messages):
            if isinstance(m, dict) and m.get("role") == "system":
                out.append(m)
        # (b) head-protected non-system messages (stock keep law), transcript order
        non_system = [i for i, m in enumerate(messages)
                      if isinstance(m, dict) and m.get("role") != "system"]
        for i in non_system[: self._protect_first_n]:
            self._emit_transcript_slot(out, messages, units, i, removed_ids, removed_results, stubbed_results)
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
            self._emit_transcript_slot(out, messages, units, i, removed_ids, removed_results, stubbed_results)
        return out

    def _stub_message(self, u: _PageUnit, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Part C: a RECOVERABLE stub for a dropped tool result — tool name,
        arguments and a re-run hint ONLY. Never the result body, value or code.
        Pure dict/string work (L7): no write, socket or spawn."""
        src = messages[u.call_index] if 0 <= u.call_index < len(messages) else None
        call = None
        if isinstance(src, dict):
            for c in (src.get("tool_calls") or []):
                if isinstance(c, dict) and c.get("id") == u.call_id:
                    call = c
                    break
        if isinstance(call, dict):
            fn = call.get("function")
            if not isinstance(fn, dict):
                fn = {}
            name = fn.get("name") or call.get("name") or "tool"
            raw_args = fn.get("arguments") or call.get("arguments") or ""
            # Part C fix: arguments are an injection + size surface (Part II
            # §7.3/§12.4). The producing call stays in the carrier, so the
            # arguments are already in the request: MUTATING tools (write,
            # execute — anything outside the read-only table) get NO excerpt;
            # read-only tools get a capped, frame-escaped one.
            if name in _STUB_READ_ONLY_TOOLS:
                args = _stub_arg_excerpt(raw_args)
            else:
                args = "see the call above"
        else:
            name, args = "tool", "see the call above"
        return {"role": "tool", "tool_call_id": u.call_id,
                "content": f"[ctxvm: dropped result for {name}({args}); re-run to restore.]"}

    def _emit_transcript_slot(self, out: List[Dict[str, Any]], messages: List[Dict[str, Any]],
                              units: Dict[int, _PageUnit], i: int,
                              removed_ids: Set[str], removed_results: Set[int],
                              stubbed: Set[int]) -> None:
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
                if i in stubbed:
                    stub = self._stub_message(u, messages)
                    self._stub_rows.append({"ids": sorted(u.id_toks),
                                            "stubText": stub["content"]})
                    out.append(stub)
                return  # verbatim page rides the block; a stub is recoverable, not the body
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
                 protect_first_n: int = 3, protect_last_n: int = 6,
                 selection_mode: Optional[str] = None,
                 stub_dropped: Optional[str] = None,
                 shadow_selection: Optional[bool] = None) -> Optional[Any]:
    """Registration-time factory. Returns None outside the hermes runtime (the
    plugin's observer duties never depend on the engine — the registration in
    live/__init__.py is fail-open)."""
    if not _HOST_ABC:
        return None
    return CtxvmFaultPinEngine(v_budget=v_budget, selection_mode=selection_mode,
                               protect_first_n=protect_first_n,
                               protect_last_n=protect_last_n,
                               stub_dropped=stub_dropped,
                               shadow_selection=shadow_selection)
