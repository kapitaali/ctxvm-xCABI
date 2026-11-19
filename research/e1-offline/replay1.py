#!/usr/bin/env python3
"""E1 offline replay. No model call, no spend, no network. --list does not score."""
import sys, os, json, glob, hashlib, random, collections, importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('view_v1', os.path.join(ROOT, 'view-v1.py'))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
view_v1 = mod.view_v1
SOURCES = ('identifier_scan', 'tool_recall')
MAX_EVENTS = 20000

def emit(s):
    print(s, flush=True)

def zero():
    return collections.Counter({s: 0 for s in SOURCES})

def load_manifest():
    entries = {}
    for line in open(os.path.join(ROOT, 'manifest.sha256')):
        line = line.strip()
        if not line or line.startswith('#') or '  ' not in line:
            continue
        h, name = line.split('  ', 1)
        entries[name] = h
    return entries

def verify_manifest():
    entries = load_manifest()
    bad = []
    for name, h in entries.items():
        p = os.path.join(ROOT, name)
        if not os.path.exists(p) or hashlib.sha256(open(p, 'rb').read()).hexdigest() != h:
            bad.append(name)
    return len(entries), bad

def run_file(path, seed):
    events = [json.loads(l) for l in open(path) if l.strip()]
    if len(events) > MAX_EVENTS:
        raise ValueError(f'bounded input exceeded: {len(events)} > {MAX_EVENTS}')
    v1 = view_v1(events); v2 = view_v1(events)
    if json.dumps(v1, sort_keys=True) != json.dumps(v2, sort_keys=True):
        raise ValueError('view non-deterministic on second pass')
    declared = v1['declaredRefs']
    control, arm_a, arm_b = zero(), zero(), zero()
    removed_a, removed_b = set(), set()
    rng = random.Random(seed)
    for t in v1['turns']:
        named = []
        for f in t['faults']:
            src = f['source'] if f['source'] in SOURCES else 'other'
            ref = f['logicalRef']
            if ref is not None and ref not in removed_a: arm_a[src] += 1
            if ref is not None and ref not in removed_b: arm_b[src] += 1
            if src in SOURCES: control[src] += 1
            if ref and ref not in named: named.append(ref)
        for ref in named: removed_a.add(ref)
        k = len(named)
        if k:
            pool = [r for r in declared if r not in removed_b]
            for r in rng.sample(pool, min(k, len(pool))): removed_b.add(r)
    return {'turns': len(v1['turns']), 'control': dict(control), 'A': dict(arm_a), 'B': dict(arm_b),
            'events': len(events), 'declared': len(declared), 'faulted': len(v1['faultedRefs'])}

def aggregate(rows):
    out = {'turns': 0, 'control': zero(), 'A': zero(), 'B': zero()}
    for r in rows:
        out['turns'] += r['turns']
        for arm in ('control', 'A', 'B'):
            for s in SOURCES: out[arm][s] += r[arm][s]
    for arm in ('control', 'A', 'B'): out[arm] = dict(out[arm])
    return out

def report_counts(agg):
    emit('COUNTS ' + json.dumps(agg, sort_keys=True))
    rates = {arm: {s: (agg[arm][s] / agg['turns'] if agg['turns'] else 0.0) for s in SOURCES}
             for arm in ('control', 'A', 'B')}
    emit('RATES ' + json.dumps(rates, sort_keys=True))
    return rates

def apply_stop(agg, rates):
    n = {'identifier_scan': agg['control']['identifier_scan'], 'tool_recall': agg['control']['tool_recall']}
    emit('SOURCE_N ' + json.dumps(n, sort_keys=True))
    if n['tool_recall'] < 10:
        return 'BLOCKED: tool_recall n<10', {}
    adv = {s: ((rates['B'][s] - rates['A'][s]) / rates['control'][s]) if rates['control'][s] else 0.0
           for s in SOURCES}
    emit('ADVANTAGE ' + json.dumps(adv, sort_keys=True))
    negative = {s: (adv[s] <= 0.10) for s in SOURCES}
    emit('PER_SOURCE ' + json.dumps(negative, sort_keys=True))
    if all(negative.values()):
        return 'NEGATIVE RESULT: labels indistinguishable from random on both sources', adv
    if negative['tool_recall'] and not negative['identifier_scan']:
        return 'MIXED: tool_recall negative; identifier_scan signal only', adv
    return 'LABEL-QUALITY SIGNAL ONLY: no answer/model claim; E2 still owner-gated', adv

def main():
    nfiles, bad = verify_manifest()
    if bad: emit('MANIFEST_FAIL ' + json.dumps(bad)); sys.exit(2)
    paths = sorted(glob.glob(os.path.join(ROOT, 'traces', '*.jsonl')))
    if '--list' in sys.argv[1:]:
        emit('MODE list-only — no scoring, no model call')
        emit(f'MANIFEST_OK entries={nfiles} traces={len(paths)}')
        emit('EXPECTED identifier_scan=41 tool_recall=21 paths=15 fault_bearing')
        for p in paths: emit('FILE ' + os.path.basename(p))
        sys.exit(0)
    if len(paths) != 17:
        emit(f'FAIL unexpected trace count {len(paths)}'); sys.exit(2)
    rows = []
    for p in paths:
        name = os.path.basename(p)
        emit('START ' + name)
        try:
            seed = int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)
            r = run_file(p, seed); rows.append({'name': name, **r})
            emit(f'OK {name} events={r["events"]} turns={r["turns"]} '
                 f'id={r["control"]["identifier_scan"]}/{r["A"]["identifier_scan"]}/{r["B"]["identifier_scan"]} '
                 f'tool={r["control"]["tool_recall"]}/{r["A"]["tool_recall"]}/{r["B"]["tool_recall"]}')
        except Exception as e:
            emit(f'FAIL {name} {type(e).__name__}: {str(e)[:160]}')
    agg = aggregate(rows)
    c = json.load(open(os.path.join(ROOT, 'fault-counts.json')))['total']
    reproduce = (agg['control'].get('identifier_scan') == c.get('identifier_scan') and
                 agg['control'].get('tool_recall') == c.get('tool_recall'))
    emit('SOURCE_REPRODUCE ' + str(reproduce).lower())
    rates = report_counts(agg)
    verdict, adv = apply_stop(agg, rates)
    emit('VERDICT ' + verdict)
    with open(os.path.join(ROOT, 'result.json'), 'w') as f:
        json.dump({'date': '2026-11-18', 'view': 'v1:150d24ca', 'files': rows, 'aggregate': agg,
                   'rates': rates, 'source_reproduce': reproduce, 'advantage': adv,
                   'verdict': verdict, 'model_calls': 0}, f, indent=2)
    emit('WROTE result.json')

if __name__ == '__main__': main()
