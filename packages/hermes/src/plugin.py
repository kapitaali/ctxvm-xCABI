"""
ctxvm Hermes plugin core — telemetry-first tracer for Hermes agent loops.

Pure Python port of `@ctxvm/node` (packages/node/src/tracer.ts) adapted to the
Hermes hook surface (see packages/hermes/HOOKS.md for the pin). Zero runtime
dependencies beyond stdlib. Mirror-only v0: records; never evicts, never mutates
caller data, never throws on semantic conditions.

Public surface (mirrors the T6/T7 contract):

    vm = createCtxvmPlugin(init)
    vm.on_session_start(payload)     # on_session_start hook → session.open
    vm.on_pre_tool_call(payload)     # pre_tool_call hook → recall({tool, args})
    vm.on_post_tool_call(payload)    # post_tool_call hook → page.declare (completed only)
    vm.on_pre_llm_call(payload)      # pre_llm_call hook → scan(history) + render()
    vm.on_session_end(payload)       # on_session_end hook → finishAll() flush
    vm.finish_all()                  # → [{sessionID, trace}] for all sessions
    vm.tracer_for(session_id)        # Tracer access for tests
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union

Json = Union[None, bool, int, float, str, List["Json"], Dict[str, "Json"]]

ARGS_LIMIT = 120


def canonical_json(value: Json) -> str:
    """Comparator-stable canonical JSON: recursively sorted object keys, minimal separators."""
    if value is None or not isinstance(value, (dict, list)):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(v) for v in value) + "]"
    sorted_keys = sorted(value.keys())
    body = ",".join(f"{json.dumps(k)}:{canonical_json(value[k])}" for k in sorted_keys)
    return "{" + body + "}"


def content_hash(content: str) -> str:
    """sha256:<8 hex> — content-identity digest form used by the reference fixtures (RFC-0 §6)."""
    hex_digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
    return f"sha256:{hex_digest}"


def hex8(content: str) -> str:
    return content_hash(content)[len("sha256:"):]


def approx4(content: str) -> int:
    """Declared-token approximation apx4-char — documented v0 baseline."""
    return math.ceil(len(content) / 4) if content else 0


def tool_ref(server: Optional[str], name: str, args: Json) -> str:
    """tool:<server>.<name>(<canonicalArgs>); >120-char args truncate with #sha8 tail."""
    canonical = canonical_json(args)
    if len(canonical) <= ARGS_LIMIT:
        trimmed = canonical
    else:
        trimmed = canonical[:ARGS_LIMIT] + "#" + hex8(canonical)
    prefix = f"{server}.{name}" if server else name
    return f"tool:{prefix}({trimmed})"


def file_ref(path: str) -> str:
    return f"file:{path}"


def declare_latency_ms(value: Any) -> Optional[int]:
    """RFC-0.1 §R4 strict intake for `page.declare.latencyMs` (R5-turn card).

    Mirrors the node `declareLatencyOf` / `providerUsageOf` law: whole
    milliseconds >= 0 only. `bool` is excluded explicitly because bool IS an int
    in Python — `True` must never become 1 ms. Anything else is an ABSENCE (the
    key is omitted), never null and never float-coerced.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def identity_tokens(logical_ref: str) -> List[str]:
    """Identity candidates a page exposes to identifier_scan: ref fragments, longest first."""
    body = logical_ref.split(":", 1)[1] if ":" in logical_ref else logical_ref
    import re
    inner_match = re.match(r"^([^(]*)\((.*)\)$", body)
    arg_zone = inner_match.group(2) if inner_match else body
    tokens: Set[str] = set()
    tokens.add(body)
    if inner_match:
        tokens.add(inner_match.group(1))
    for m in re.finditer(r'"([^"]+)"', arg_zone):
        tokens.add(m.group(1))
    for m in re.finditer(r"[A-Za-z0-9][\w./:-]{5,}", body):
        tokens.add(m.group(0))
    return sorted((t for t in tokens if len(t) >= 3), key=len, reverse=True)


PageKind = str  # "file" | "tool_result" | "summary" | "image_ref"
FaultSource = str  # "tool_recall" | "identifier_scan" | "explicit_api" | "semantic"


class TraceInit:
    def __init__(self, agent_id: str, model: str, provider: str,
                 budget_tokens: int, tokenizer_id: str = "apx4-char"):
        self.agent_id = agent_id
        self.model = model
        self.provider = provider
        self.budget_tokens = budget_tokens
        self.tokenizer_id = tokenizer_id


class FinishedTrace:
    def __init__(self, jsonl: str, events: List[Dict[str, Any]], stats: Dict[str, Any]):
        self.jsonl = jsonl
        self.events = events
        self.stats = stats


class Tracer:
    """Per-session RFC-0 xCABI tracer. Mirrors @ctxvm/node createTrace()."""

    def __init__(self, init: TraceInit):
        self._init = init
        self._events: List[Dict[str, Any]] = []
        self._tokenizer_id = init.tokenizer_id
        self._declared: Dict[str, Dict[str, Any]] = {}  # key = logicalRef
        self._pending_recall: Set[str] = set()
        self._touched: Set[str] = set()  # dedupe per page·source
        self._turn = -1
        self._fault_count = 0
        self._all_declared: Dict[str, int] = {}  # ref|hash → tokens
        self._pending_meta: List[Dict[str, Any]] = []
        # RFC-0.1 §R4 (D9 policy): every event gains `ts` — RFC 3339 UTC ms.
        # DEFAULT ON; the per-trace opt-out `CTXVM_TRACE_TS=0` (read ONCE at
        # trace creation) covers byte-stability needs (fixtured drops,
        # determinism pins). Tail stamps mint at the turn's render snapshot
        # time, so repeated finish() flushes re-derive the SAME stamps — the
        # idempotency law below holds under default-on (RR-R4TS2, node mirror).
        self._ts_enabled: bool = os.environ.get("CTXVM_TRACE_TS") != "0"
        self._turn_stamps: List[Optional[str]] = []
        # session.open is emitted at tracer creation (first event in the log).
        # RFC-0.1 R0 (D4 approved; D8 = emitter version switch first): every
        # trace this build emits declares schemaVersion "0.1" — the version
        # boundary. Shipped corpus drops (m1–m8) and the frozen package
        # fixtures stay v0: committed golden bytes, never regenerated.
        self._push({
            "type": "session.open",
            "agentId": init.agent_id,
            "model": init.model,
            "provider": init.provider,
            "budgetTokens": init.budget_tokens,
            "tokenizerId": init.tokenizer_id,
            "schemaVersion": "0.1",
        })

    def _stamp(self) -> str:
        """RFC-3339 UTC, millisecond precision — exactly the v0.1 schema's ts
        pattern (§R4). Mirror of the node tracer's ``Date#toISOString()``."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S") + f".{now.microsecond // 1000:03d}Z"

    def _push(self, event: Dict[str, Any]) -> None:
        # RFC-0.1 §R4: ts rides LAST on every event — the canonical v0.1 wire
        # order the rust writer minted (events-v0-1.jsonl: …, providerUsage, ts).
        # Assignment order lands it after the body keys. Optional per the §R4
        # law — under the opt-out the key is absent, never null.
        if self._ts_enabled:
            event["ts"] = self._stamp()
        self._events.append(event)

    def _emit_fault(self, page: Dict[str, Any], source: FaultSource,
                    latency_ms: Optional[int]) -> None:
        dedupe_key = f"{page['logicalRef']}|{source}"
        if dedupe_key in self._touched:
            return
        self._touched.add(dedupe_key)
        self._fault_count += 1
        t = self._turn if self._turn >= 0 else 0
        event: Dict[str, Any] = {
            "type": "page.fault",
            "turn": t,
            "page": {"logicalRef": page["logicalRef"], "contentHash": page["contentHash"]},
            "source": source,
        }
        if latency_ms is not None:
            event["latencyMs"] = latency_ms
        self._push(event)

    def _reveal(self, page: Dict[str, Any], turn: int) -> None:
        self._push({
            "type": "page.render",
            "turn": turn,
            "page": {"logicalRef": page["logicalRef"], "contentHash": page["contentHash"]},
            "mode": "full",
        })
        page["revealed"] = True

    def _declare_page(self, ref: str, hash_val: str, kind: str, tokens: int,
                      latency_ms: Optional[int]) -> None:
        """RFC-0.1 §R5 + §R4 (R5-turn card): `page.declare` carries the tracer's
        turn counter AT DECLARATION TIME; declarations made before the first
        render carry -1 and stamp as 0 (the RFC-0 §5 convention `_emit_fault`
        already uses). `latencyMs` rides between `turn` and `ts` only when the
        caller supplied a valid one — `ts` lands LAST via `_push`.
        """
        t = self._turn if self._turn >= 0 else 0
        event: Dict[str, Any] = {
            "type": "page.declare",
            "page": {"id": {"logicalRef": ref, "contentHash": hash_val}, "kind": kind,
                     "tokens": tokens},
            "turn": t,
        }
        if latency_ms is not None:
            event["latencyMs"] = latency_ms
        self._push(event)

    def page(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Declare a page from tool result content. Returns {logicalRef, contentHash, tokens}."""
        content = input["content"]
        content_str = content if isinstance(content, str) else canonical_json(content)
        hash_val = content_hash(content_str)
        ref = input.get("ref") or tool_ref(input.get("server"), input.get("tool") or "unknown",
                                        input.get("args", None))
        tokens = input.get("tokens") or approx4(content_str)
        kind = input.get("kind") or ("image_ref" if isinstance(content, str)
                                     and content_str.startswith("http") else "tool_result")
        latency_ms = declare_latency_ms(input.get("latencyMs"))

        existing = self._declared.get(ref)
        if existing is None:
            page: Dict[str, Any] = {
                "logicalRef": ref,
                "contentHash": hash_val,
                "kind": kind,
                "tokens": tokens,
                "revealed": False,
                "revealedAtPrev": False,
                "identities": identity_tokens(ref),
            }
            self._declared[ref] = page
            self._all_declared[f"{ref}|{hash_val}"] = tokens
            self._declare_page(ref, hash_val, kind, tokens, latency_ms)
            self._pending_recall.discard(ref)
            return {"logicalRef": ref, "contentHash": hash_val, "tokens": tokens}

        if existing["contentHash"] == hash_val:
            if ref in self._pending_recall:
                self._pending_recall.discard(ref)
                self._emit_fault(existing, "tool_recall", None)
        else:
            existing["contentHash"] = hash_val
            existing["tokens"] = tokens
            existing["kind"] = kind
            existing["revealed"] = False
            existing["revealedAtPrev"] = False
            self._all_declared[f"{ref}|{hash_val}"] = tokens
            self._declare_page(ref, hash_val, kind, tokens, latency_ms)
            self._pending_recall.discard(ref)
        return {"logicalRef": ref, "contentHash": existing["tokens"] and existing["contentHash"]
                or hash_val, "tokens": existing["tokens"]}

    def recall(self, input: Dict[str, Any]) -> None:
        """Mark a pre-execution re-call (tool.execute.before)."""
        ref = input.get("ref") or tool_ref(input.get("server"), input.get("tool") or "unknown",
                                        input.get("args", None))
        if ref in self._declared:
            self._pending_recall.add(ref)

    def render(self, input: Optional[Dict[str, Any]] = None) -> None:
        """Turn boundary: reveals newly declared pages; turn-level facts flush at finish()."""
        input = input or {}
        self._turn += 1
        for page in self._declared.values():
            if not page["revealed"]:
                self._reveal(page, self._turn)

        hit = 0
        resident_at_turn = 0
        for page in self._declared.values():
            if page["revealedAtPrev"]:
                hit += page["tokens"]
            resident_at_turn += page["tokens"]
            page["revealedAtPrev"] = page["revealed"]

        # §R4-ts: the turn's tail facts (turn.render + this call.meta snapshot)
        # mint ONE timestamp at snapshot time — finish() flushes re-derive
        # these exact bytes (node mirror: the same `now` for both).
        now: Optional[str] = self._stamp() if self._ts_enabled else None
        self._turn_stamps.append(now)
        self._pending_meta.append({
            "turn": self._turn,
            "hit": hit,
            "residentAtTurn": resident_at_turn,
            "latencyMs": input.get("latencyMs"),
            "ts": now,
        })

    def scan(self, input: Dict[str, Any]) -> None:
        """identifier_scan over produced model text (deduped per page per source)."""
        text = input["text"]
        latency_ms = input.get("latencyMs")
        for page in self._declared.values():
            for tok in page["identities"]:
                if tok in text:
                    self._emit_fault(page, "identifier_scan", latency_ms)
                    break

    def pin(self, input: Dict[str, Any]) -> None:
        page = self._declared.get(input["ref"])
        if page is None:
            return
        self._push({
            "type": "page.pin",
            "page": {"logicalRef": page["logicalRef"], "contentHash": page["contentHash"]},
            "reason": input["reason"],
        })

    def unpin(self, input: Dict[str, Any]) -> None:
        page = self._declared.get(input["ref"])
        if page is None:
            return
        self._push({
            "type": "page.unpin",
            "page": {"logicalRef": page["logicalRef"], "contentHash": page["contentHash"]},
            "reason": input["reason"],
        })

    def finish(self) -> FinishedTrace:
        """Flush: turn.render × (turn+1) then call.meta × len(pending_meta).

        Idempotent: the tail is computed per call and never appended to
        ``_events``, so repeated flushes (session end, unload, atexit) produce
        the same JSONL instead of duplicating turn/meta records.
        """
        resident = sum(self._all_declared.values())
        turn = self._turn
        tail: List[Dict[str, Any]] = []
        for t in range(turn + 1):
            tr: Dict[str, Any] = {
                "type": "turn.render",
                "turn": t,
                "residentTokens": resident,
                "evictedTokens": 0,
            }
            if self._init.budget_tokens > 0:
                tr["headroom"] = self._init.budget_tokens - resident
            # §R4-ts: cached from snapshot time — repeated flushes stay
            # byte-stable (idempotency law). Turn index aligns with render order.
            stamp = self._turn_stamps[t]
            if stamp is not None:
                tr["ts"] = stamp
            tail.append(tr)

        for m in self._pending_meta:
            meta: Dict[str, Any] = {
                "type": "call.meta",
                "turn": m["turn"],
                "provider": self._init.provider,
                "cacheEstimate": {
                    "estHitTokens": m["hit"],
                    "estMissTokens": m["residentAtTurn"] - m["hit"],
                    "providerReported": False,
                },
            }
            if m.get("latencyMs") is not None:
                meta["latencyMs"] = m["latencyMs"]
            # §R4-ts rides LAST (the wire slot where providerUsage would ride
            # first if this port's hook surface ever gains a usage source —
            # the §R3 per-lane omission law; see 09-plugin-parity.md §2).
            if m.get("ts") is not None:
                meta["ts"] = m["ts"]
            tail.append(meta)

        events = list(self._events) + tail
        jsonl = "".join(json.dumps(e) + "\n" for e in events)
        stats = {
            "turns": turn + 1,
            "pages": len(self._all_declared),
            "faults": self._fault_count,
            "residentTokens": resident,
        }
        return FinishedTrace(jsonl=jsonl, events=events, stats=stats)


def infer_kind(content: Json) -> PageKind:
    s = content if isinstance(content, str) else canonical_json(content)
    return "image_ref" if s.startswith("http") else "tool_result"


# Hermes knows the model/provider of the running session; the tracer should not have to
# be told through env vars. These are the keys seen across Hermes hook payload versions.
_IDENTITY_KEYS = (("model", ("model", "model_name", "model_id", "modelID")),
                  ("provider", ("provider", "provider_name", "provider_id", "providerID")))
# opencode's hook carries `model: {id, providerID, variant}`; assume nothing about nesting.
_IDENTITY_NESTED = (("model", ("id", "modelID", "model")),
                    ("provider", ("providerID", "provider_id", "provider")))


def identity_from_payload(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Extract {model, provider} from a hook payload when the host provides them.

    Flat keys first, then the nested `model` object shape the opencode surface uses.
    Anything the host does not send stays unset and falls back to env at the call site.
    """
    found: Dict[str, str] = {}
    for field, keys in _IDENTITY_KEYS:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                found[field] = value.strip()
                break
    nested = payload.get("model")
    if isinstance(nested, dict):
        for field, keys in _IDENTITY_NESTED:
            if field in found:
                continue
            for key in keys:
                value = nested.get(key)
                if isinstance(value, str) and value.strip():
                    found[field] = value.strip()
                    break
    return found or None


class CtxvmPlugin:
    """Per-session tracer manager for Hermes. Mirrors @ctxvm/opencode createCtxvmPlugin."""

    def __init__(self, init: TraceInit):
        self._init = init
        self._tracers: Dict[str, Tracer] = {}

    def _vm_for(self, session_id: str, identity: Optional[Dict[str, str]] = None) -> Tracer:
        """Tracer for a session; `identity` overrides the process-level model/provider."""
        existing = self._tracers.get(session_id)
        if existing is not None:
            return existing
        init = self._init
        if identity:
            init = TraceInit(
                agent_id=init.agent_id,
                model=identity.get("model") or init.model,
                provider=identity.get("provider") or init.provider,
                budget_tokens=init.budget_tokens,
                tokenizer_id=init.tokenizer_id,
            )
        created = Tracer(init)
        self._tracers[session_id] = created
        return created

    # --- Hermes hook handlers -------------------------------------------------

    def on_session_start(self, payload: Dict[str, Any]) -> None:
        """on_session_start hook: creates a per-session tracer (session.open emitted at creation)."""
        session_id = payload.get("session_id", "")
        self._vm_for(session_id, identity_from_payload(payload))

    def on_pre_tool_call(self, payload: Dict[str, Any]) -> None:
        """pre_tool_call hook: recall({tool, args})."""
        session_id = payload.get("session_id", "")
        vm = self._vm_for(session_id)
        tool = payload.get("tool") or payload.get("tool_name")
        vm.recall({"tool": tool, "args": payload.get("args")})

    def on_post_tool_call(self, payload: Dict[str, Any]) -> None:
        """post_tool_call hook: page.declare when status == completed (T6 §2: errors produce no page).

        Real Hermes taxonomy (model_tools.py:_tool_result_observer_fields,
        line 656-671): status is "ok" on success, "error" on failure.
        hooks.py demo payloads use "completed"/"error"; accept both.

        Hermes tool results can be a plain string, a dict with a 'content'
        list, or other shapes — handle all gracefully.
        """
        status = payload.get("status")
        if status not in ("ok", "completed"):
            return
        session_id = payload.get("session_id", "")
        vm = self._vm_for(session_id)
        result = payload.get("result")
        body = extract_page_body(result)
        tool = payload.get("tool") or payload.get("tool_name")
        vm.page({
            "tool": tool,
            "args": payload.get("args"),
            "content": body,
        })

    def on_pre_llm_call(self, payload: Dict[str, Any]) -> None:
        """pre_llm_call hook: scan conversation history for identifiers, then render turn boundary."""
        session_id = payload.get("session_id", "")
        vm = self._vm_for(session_id, identity_from_payload(payload))
        history = payload.get("conversation_history") or []
        text = self._transcript_texts(history)
        vm.scan({"text": text, "latencyMs": payload.get("latencyMs")})
        vm.render({"latencyMs": payload.get("latencyMs")})

    def on_session_end(self, payload: Dict[str, Any]) -> None:
        """on_session_end hook: no per-session action here; flush is driven by finish_all()."""
        pass  # flush is explicit via finish_all() from the adapter's cleanup

    # --- Tracer access --------------------------------------------------------

    def finish_all(self) -> List[Dict[str, Any]]:
        """Flush every session tracer. Returns [{sessionID, trace}] sorted by sessionID."""
        out = []
        for session_id in sorted(self._tracers.keys()):
            vm = self._tracers[session_id]
            out.append({"sessionID": session_id, "trace": vm.finish()})
        return out

    def tracer_for(self, session_id: str) -> Tracer:
        return self._vm_for(session_id)

    # --- Helpers --------------------------------------------------------------

    @staticmethod
    def _content_to_page_body(content_items: List[Dict[str, Any]]) -> str:
        """Page body from Tool.Result.content: text items verbatim joined by \n;
        non-text items as deterministic type markers (same as T9)."""
        kept = []
        for item in content_items:
            item_type = item.get("type") or "text"
            if item_type == "text":
                kept.append(item.get("text", ""))
            else:
                name = item.get("name")
                kept.append(f"<{item_type}{f':{name}' if isinstance(name, str) else ''}>")
        return "\n".join(kept)

    @staticmethod
    def _transcript_texts(messages: List[Dict[str, Any]]) -> str:
        """All text entering the compose window this turn (user + assistant + tool summaries).

        Shapes seen in the wild (Hermes v0.22.5): ``content`` as a plain string
        (agent/conversation_loop.py:350, oneshot.py:103), as a list of content
        blocks (multimodal / OpenCode-style), and ``parts`` (OpenCode recordings).
        """
        parts: List[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            zone = message.get("parts") or message.get("content")
            if isinstance(zone, str):
                parts.append(zone)                      # the live shape (W4b B1)
            elif isinstance(zone, list):
                for part in zone:
                    if isinstance(part, dict) and part.get("text"):
                        parts.append(part["text"])
                    elif isinstance(part, str):
                        parts.append(part)
            elif message.get("text"):
                parts.append(message["text"])
        return "\n".join(parts)


def extract_page_body(result: Any) -> str:
    """Extract page body from any tool result type.

    Hermes tool results can be:
    - str: plain text output → used verbatim
    - dict with 'content' list: structured result (OpenCode-style)
    - dict with 'text' key: direct text
    - list: array of content items
    - other: stringified
    """
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        content = result.get("content")
        if content is None:
            text = result.get("text")
            return text if isinstance(text, str) else ""
        if isinstance(content, list):
            return items_to_body(content)
        return ""
    if isinstance(result, list):
        return items_to_body(result)
    return str(result)


def items_to_body(items: list) -> str:
    """Convert content items to page body: text items verbatim, non-text as markers."""
    kept = []
    for item in items:
        if isinstance(item, str):
            kept.append(item)
        elif isinstance(item, dict):
            item_type = item.get("type") or "text"
            if item_type == "text":
                kept.append(item.get("text", ""))
            else:
                name = item.get("name")
                kept.append(f"<{item_type}{f':{name}' if isinstance(name, str) else ''}>")
    return "\n".join(kept)


def create_ctxvm_plugin(init: Dict[str, Any]) -> CtxvmPlugin:
    """Factory: create_ctxvm_plugin({agentId, model, provider, budgetTokens, tokenizerId?})."""
    trace_init = TraceInit(
        agent_id=init["agentId"],
        model=init["model"],
        provider=init["provider"],
        budget_tokens=init["budgetTokens"],
        tokenizer_id=init.get("tokenizerId", "apx4-char"),
    )
    return CtxvmPlugin(trace_init)
