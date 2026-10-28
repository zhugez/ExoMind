#!/usr/bin/env python3
"""Offline retrieval experiment, NOT a reproduction of Zero-Mem. Stdlib only."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import re
import statistics
import subprocess
import tempfile
import time
import unicodedata


# Match ExoMind's tokenizer to avoid a tokenizer advantage in the comparison.
def tokens(text):
    folded = ''.join('d' if c in ('đ', 'Đ') else c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9_-]+", folded.lower())


def bm25(documents, query):
    counts = [Counter(tokens(d)) for d in documents]
    average = sum(map(lambda c: sum(c.values()), counts)) / max(1, len(counts))
    frequency = Counter(t for c in counts for t in c)
    scores = []
    for count in counts:
        score = 0.0
        for term in set(tokens(query)):
            tf = count[term]
            if tf:
                idf = math.log(1 + (len(counts) - frequency[term] + 0.5) / (frequency[term] + 0.5))
                score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * sum(count.values()) / average))
        scores.append(score)
    return scores


def normalize(scores):
    peak = max(scores, default=0)
    return [s / peak if peak else 0.0 for s in scores]


class Inspired:
    def __init__(self, notes):
        self.notes = notes
        self.units = []
        for name, text in sorted(notes.items()):
            lines = text.splitlines()
            start = 0
            while start < len(lines):
                while start < len(lines) and not lines[start].strip():
                    start += 1
                end = start
                while end < len(lines) and lines[end].strip():
                    end += 1
                if start < end:
                    self.units.append({"path": name, "start": start + 1, "end": end,
                                       "text": "\n".join(lines[start:end])})
                start = end + 1
        self.edges = defaultdict(set)
        self.entities = set()
        for i, unit in enumerate(self.units):
            # ponytail: capitalization heuristic misses aliases/common nouns; use NER if this experiment warrants it.
            entities = set(re.findall(r"\b[A-Z][A-Za-z0-9_-]{2,}\b", unit["text"]))
            for entity in entities - {"The", "Current", "Previous", "After", "Before"}:
                key = "e:" + entity.lower()
                self.entities.add(key)
                self.edges[i].add(key)
                self.edges[key].add(i)
            if i and self.units[i - 1]["path"] == unit["path"]:
                self.edges[i].add(i - 1)
                self.edges[i - 1].add(i)
        self.names = sorted(notes)

    def search(self, query, topk=5, graph=True):
        if topk < 1:
            raise ValueError("topk must be positive")
        local = normalize(bm25([u["text"] for u in self.units], query))
        document = normalize(bm25([self.notes[p] for p in self.names], query))
        doc_scores = dict(zip(self.names, document))
        hierarchy = normalize([0.7 * s + 0.3 * doc_scores[u["path"]]
                               for s, u in zip(local, self.units)])
        scores = hierarchy
        if graph and sum(local):
            reset = {i: s for i, s in enumerate(local) if s}
            for term in set(tokens(query)):
                if "e:" + term in self.entities:
                    reset["e:" + term] = 1.0
            total = sum(reset.values())
            reset = {key: value / total for key, value in reset.items()}
            rank = dict(reset)
            # Fixed bounded PPR iterations; no query-time LLM or semantic embeddings.
            for _ in range(20):
                nxt = defaultdict(float, {key: 0.4 * value for key, value in reset.items()})
                dangling = 0.0
                for node, value in rank.items():
                    neighbors = self.edges[node]
                    if neighbors:
                        for other in neighbors:
                            nxt[other] += 0.6 * value / len(neighbors)
                    else:
                        dangling += 0.6 * value
                for node, value in reset.items():
                    nxt[node] += dangling * value
                rank = nxt
            relational = normalize([rank.get(i, 0.0) for i in range(len(self.units))])
            temporal = bool(re.search(r"\b(current|latest|before|after|when|date)\b", query.lower()))
            weight = 0.4 if temporal else 0.6
            scores = [weight * g + (1 - weight) * h for g, h in zip(relational, hierarchy)]
        ranked = sorted(range(len(scores)), key=lambda i: (-scores[i], self.units[i]["path"], i))
        results, seen = [], set()
        for i in ranked:
            unit = self.units[i]
            if scores[i] <= 0 or unit["path"] in seen:
                continue
            seen.add(unit["path"])
            # Bounded source-local closure: keep verbatim neighboring paragraphs.
            evidence = [self.units[j] for j in range(max(0, i - 1), min(len(self.units), i + 2))
                        if self.units[j]["path"] == unit["path"]]
            results.append({"path": unit["path"], "score": scores[i], "evidence": evidence})
            if len(results) == topk:
                break
        return results


def metrics(rankings, queries):
    out = {}
    for k in (1, 3, 5):
        out[f"hit@{k}"] = statistics.mean(bool(set(r[:k]) & set(q["expected"]))
                                         for r, q in zip(rankings, queries))
        out[f"all_evidence@{k}"] = statistics.mean(set(q["expected"]) <= set(r[:k])
                                                  for r, q in zip(rankings, queries))
    out["mrr@5"] = statistics.mean(next((1 / (i + 1) for i, p in enumerate(r[:5])
                                                     if p in q["expected"]), 0)
                                         for r, q in zip(rankings, queries))
    return out


def run(exom, fixture):
    notes, queries = fixture["notes"], fixture["queries"]
    if not notes or not queries:
        raise ValueError("fixture must contain notes and queries")
    for name in notes:
        p = Path(name)
        if p.is_absolute() or ".." in p.parts or p.parts[0] not in {
            "00_Inbox", "10_Projects", "20_Areas", "30_Resources", "99_Archives"
        } or p.suffix != ".md":
            raise ValueError(f"invalid fixture note path: {name}")
    for q in queries:
        if not q["expected"] or not set(q["expected"]) <= set(notes):
            raise ValueError("expected paths must reference fixture notes")
    with tempfile.TemporaryDirectory(prefix="exom-inspired-") as tmp:
        root = Path(tmp)
        for name, text in notes.items():
            target = root / "notes" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        dataset = root / "queries.json"
        dataset.write_text(json.dumps(queries))
        subprocess.run([exom, "index", "--notes-root", str(root / "notes"), "--out-root", str(root / "index")],
                       check=True, capture_output=True, text=True)
        graph = root / "index/graph.json"
        indexed = json.loads(graph.read_text())
        assert indexed["stats"]["notes"] == len(notes), "fixture was not fully indexed"
        native = json.loads(subprocess.run([exom, "benchmark", "--dataset", str(dataset),
                                           "--graph", str(graph), "--topk", "5", "--json"],
                                          check=True, capture_output=True, text=True).stdout)
        rankings = {"exomind": [], "bm25_hierarchy": [], "inspired": []}
        elapsed = defaultdict(list)
        start = time.perf_counter()
        engine = Inspired(notes)
        build_ms = (time.perf_counter() - start) * 1000
        examples = []
        for q in queries:
            rows = json.loads(subprocess.run([exom, "recall", "--query", q["query"], "--graph", str(graph),
                                              "--topk", "5", "--json"], check=True,
                                             capture_output=True, text=True).stdout)["results"]
            # Null ghost paths still consume a native result slot; do not silently remove them.
            rankings["exomind"].append([r["path"] for r in rows])
            for name, use_graph in (("bm25_hierarchy", False), ("inspired", True)):
                times = []
                for _ in range(5):
                    start = time.perf_counter()
                    results = engine.search(q["query"], graph=use_graph)
                    times.append((time.perf_counter() - start) * 1000)
                elapsed[name].append(statistics.median(times))
                rankings[name].append([r["path"] for r in results])
            examples.append({"query": q["query"], "category": q["category"], "expected": q["expected"],
                             "rankings": {name: r[-1] for name, r in rankings.items()},
                             "inspired_top1_evidence": results[0]["evidence"] if results else []})
        summary = {name: metrics(rows, queries) for name, rows in rankings.items()}
        categories = {}
        for category in sorted({q["category"] for q in queries}):
            ids = [i for i, q in enumerate(queries) if q["category"] == category]
            categories[category] = {name: metrics([rows[i] for i in ids], [queries[i] for i in ids])
                                    for name, rows in rankings.items()}
        return {"scope": "Synthetic note-level retrieval only; no QA model, no official Zero-Mem implementation",
                "notes": len(notes), "queries": len(queries), "topk": 5,
                "summary": summary, "categories": categories,
                "timing": {"exomind_rank_mean_ms": native["avg_latency_ms"],
                           "inspired_build_ms": build_ms,
                           **{f"{name}_median_query_ms": statistics.median(values)
                              for name, values in elapsed.items()},
                           "warning": "Rust ranks precomputed TF-IDF; Python recomputes BM25 per query. Not an algorithmic speed comparison."},
                "examples": examples}


def self_check():
    notes = {"10_Projects/a.md": "# Orion\n\nOrion owns Vega.\n\nVega uses Rust.",
             "10_Projects/b.md": "# Lyra\n\nLyra uses Python."}
    engine = Inspired(notes)
    assert engine.search("Orion")[0]["path"] == "10_Projects/a.md"
    assert engine.search("zzzzunseen") == []
    assert engine.search("") == []
    assert Inspired({}).search("Orion") == []
    for result in engine.search("Vega"):
        for evidence in result["evidence"]:
            lines = notes[evidence["path"]].splitlines()
            assert "\n".join(lines[evidence["start"] - 1:evidence["end"]]) == evidence["text"]
    check = metrics([["a", "b"]], [{"expected": ["a", "b"]}])
    assert check["hit@1"] == 1 and check["all_evidence@1"] == 0
    assert check["all_evidence@3"] == 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exom", default="target/release/exom")
    parser.add_argument("--fixture", type=Path, default=Path("30_Resources/Schemas/zero-mem-fixture.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    self_check()
    report = run(str(Path(args.exom).resolve()), json.loads(args.fixture.read_text()))
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(json.dumps({k: v for k, v in report.items() if k != "examples"}, indent=2))
