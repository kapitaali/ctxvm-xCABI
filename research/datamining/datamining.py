#!/usr/bin/env python3
"""Data mining over the ctxvm paper-reference database."""
import io, json, re, sqlite3, collections

DB = "/home/theb/research/anthropic-papers-reference.sqlite"
OUT = "/home/theb/Documents/ctxvm/research/datamining/datamining.json"
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = [dict(r) for r in con.execute("SELECT name,date,title,url,reference FROM papers")]

def year(r):
    m = re.match(r"(\d{4})", r["date"] or "")
    return int(m.group(1)) if m else None

def has(r, pat):
    return bool(re.search(pat, (r["title"] or "") + "\n" + (r["reference"] or ""), re.I))

THEMES = {
    "alignment_rlhf": r"\b(alignment|rlhf|human feedback|ai feedback|constitutional|preference model|reward model|rlaif)\b",
    "interpretability": r"\b(interpretability|mechanistic|sparse autoencoder|feature|circuit|activation|probe|representation)\b",
    "agents_tools": r"\b(agent|tool use|tool-call|computer use|web arena|browser|coding assistant)\b",
    "evaluation": r"\b(eval|benchmark|score|leaderboard|evaluation awareness|test set|unit test)\b",
    "monitoring_oversight": r"\b(monitor|oversight|supervis|auditing|audit|scalable oversight|anomaly detection)\b",
    "deception_sabotage": r"\b(sleeper agent|deception|scheming|sabotage|alignment faking|backdoor|reward hack|reward tampering|specification gaming)\b",
    "security_redteam": r"\b(jailbreak|red team|adversarial|prompt injection|poison|attack|security|privacy)\b",
    "context_memory": r"\b(context window|long context|memory|cache|prefix|retrieval|page|paging|compaction|summar)\b",
    "reasoning_cot": r"\b(reasoning|chain.of.thought|cot\b|thinking|reflection|self.correction|backtrack)\b",
    "rl_training": r"\b(reinforcement learning|\brl\b|policy gradient|sft|fine.tun|distill|training data|curriculum)\b",
    "multimodal": r"\b(vision|image|multimodal|video|speech|audio|vision.language)\b",
    "science_bio": r"\b(protein|clinical|medical|biology|drug|chemistry|physics|astrophys|materials)\b",
    "scaling_efficiency": r"\b(scaling law|compute|efficiency|sparse mixture|quantiz|inference cost|kv cache)\b",
    "self_improvement": r"\b(self.improv|self.train|self.refin|self.evolv|iterative sft|iterative rl|recursive|meta.learn)\b",
    "data_selection": r"\b(prioritized|active learning|data selection|curat|learnable|worth learning|filter)\b",
}

CTXVM_CONCEPTS = {
    "trace_log": r"\b(trace|log|event|record|replay|reproducib)\b",
    "page_context": r"\b(page|context window|prefix|resident|stub|evict|fault)\b",
    "counterfactual": r"\b(counterfactual|ablation|intervention|causal|attribution|leave.one.out)\b",
    "monitor_view": r"\b(monitor|view|projection|audit)\b",
    "privacy": r"\b(privacy|redact|consent|secret|personal data|gdpr)\b",
    "evaluation": r"\b(eval|benchmark|metric|score)\b",
    "failure_modes": r"\b(reward hack|sabotage|deception|jailbreak|cheat|shortcut|exploit)\b",
}

years = collections.Counter(y for y in (year(r) for r in rows) if y)
theme_counts = {t: collections.Counter() for t in THEMES}
concept_counts = {t: collections.Counter() for t in CTXVM_CONCEPTS}
theme_scientist = {t: collections.Counter() for t in THEMES}
for r in rows:
    y = year(r)
    for t, p in THEMES.items():
        if has(r, p):
            theme_counts[t][y] += 1
            theme_scientist[t][r["name"]] += 1
    for t, p in CTXVM_CONCEPTS.items():
        if has(r, p):
            concept_counts[t][y] += 1

# per-scientist counts
by_name = collections.Counter(r["name"] for r in rows)

# duplicate papers across scientists (same url)
url_names = collections.defaultdict(set)
for r in rows:
    url_names[r["url"]].add(r["name"])
shared = {u: sorted(n) for u, n in url_names.items() if len(n) > 1}

# theme co-occurrence
co = collections.Counter()
for r in rows:
    active = [t for t, p in THEMES.items() if has(r, p)]
    for i in range(len(active)):
        for j in range(i+1, len(active)):
            co[tuple(sorted((active[i], active[j])))] += 1

# buckets
def bucket(y):
    if y is None: return None
    if y <= 2022: return "2021-22"
    if y <= 2024: return "2023-24"
    return "2025-26"
buckets = collections.Counter(bucket(year(r)) for r in rows)
theme_bucket = {t: collections.Counter() for t in THEMES}
for r in rows:
    b = bucket(year(r))
    for t, p in THEMES.items():
        if has(r, p): theme_bucket[t][b] += 1

res = {
    "n_papers": len(rows), "years": dict(sorted(years.items())),
    "buckets": dict(buckets),
    "n_scientists": len(by_name),
    "top_scientists": by_name.most_common(20),
    "shared_urls": len(shared),
    "shared_examples": [(u, n) for u, n in list(shared.items())[:10]],
    "themes": {t: {"total": sum(c.values()), "by_year": dict(sorted(c.items())), "by_bucket": dict(theme_bucket[t])} for t, c in theme_counts.items()},
    "concepts": {t: {"total": sum(c.values()), "by_year": dict(sorted(c.items()))} for t, c in concept_counts.items()},
    "top_experts": {t: theme_scientist[t].most_common(5) for t in THEMES},
    "top_cooccurrence": co.most_common(20),
}
json.dump(res, open(OUT, "w"), indent=1, ensure_ascii=False, default=str)
print("wrote", OUT)
print("papers", len(rows), "years", dict(sorted(years.items())))
print("buckets", dict(buckets))
print("themes:", sorted([(t, sum(c.values())) for t, c in theme_counts.items()], key=lambda x: -x[1]))
print("concepts:", sorted([(t, sum(c.values())) for t, c in concept_counts.items()], key=lambda x: -x[1]))
