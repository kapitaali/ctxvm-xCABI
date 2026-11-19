"""E1 pure view v1. No model call, no file I/O, no randomness.

Input: parsed xCABI events. Output: per-turn declared/rendered pages, faults
by source, and resident/evicted token totals; plus sorted declared/faulted refs.
"""
VERSION = 1

def view_v1(events):
    declared_refs = set()
    faulted_refs = set()
    faults = []
    turns = {}

    def turn(n):
        k = int(n)
        if k not in turns:
            turns[k] = {"turn": k, "declared": [], "rendered": [], "faults": [],
                        "residentTokens": None, "evictedTokens": None}
        return turns[k]

    for e in events or []:
        if not isinstance(e, dict):
            continue
        t = e.get("type")
        if t == "page.declare":
            p = e.get("page") or {}
            ref = p.get("logicalRef")
            if isinstance(ref, str):
                declared_refs.add(ref)
                if not any(d["logicalRef"] == ref for d in turn(0)["declared"]):
                    turn(0)["declared"].append({"logicalRef": ref,
                                                "contentHash": p.get("contentHash"),
                                                "tokens": p.get("tokens"),
                                                "kind": p.get("kind")})
        elif t == "page.render":
            p = e.get("page") or {}
            ref = p.get("logicalRef")
            if isinstance(ref, str):
                turn(e.get("turn", 0))["rendered"].append({"logicalRef": ref, "mode": e.get("mode")})
        elif t == "page.fault":
            p = e.get("page") or {}
            ref = p.get("logicalRef") if isinstance(p.get("logicalRef"), str) else None
            src = e.get("source") if isinstance(e.get("source"), str) else "unknown"
            row = {"turn": int(e.get("turn", 0)), "logicalRef": ref, "source": src}
            faults.append(row)
            if ref:
                faulted_refs.add(ref)
            turn(e.get("turn", 0))["faults"].append({"logicalRef": ref, "source": src})
        elif t == "turn.render":
            tr = turn(e.get("turn", 0))
            tr["residentTokens"] = e.get("residentTokens") if isinstance(e.get("residentTokens"), int) else None
            tr["evictedTokens"] = e.get("evictedTokens") if isinstance(e.get("evictedTokens"), int) else None

    return {"version": VERSION,
            "turns": [turns[k] for k in sorted(turns)],
            "faults": faults,
            "declaredRefs": sorted(declared_refs),
            "faultedRefs": sorted(faulted_refs)}
