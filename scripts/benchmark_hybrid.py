#!/usr/bin/env python3
"""Evaluate a private labeled query file locally. Results can contain private queries."""
import argparse
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import tempfile
import time

try:
    from benchmark_zero_mem import metrics
    from exom_hybrid import Hybrid
except ImportError:
    from scripts.benchmark_zero_mem import metrics
    from scripts.exom_hybrid import Hybrid


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            json.dump(report, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--graph', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--queries', type=Path, required=True,
                   help='JSON {queries: [{query, expected, category?}], negative: [str]}')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--exom', default='exom')
    p.add_argument('--offline', action='store_true')
    args = p.parse_args()
    fixture = json.loads(args.queries.read_text())
    queries = fixture['queries']
    negative = fixture.get('negative', [])
    if not queries:
        p.error('queries cannot be empty')
    start = time.perf_counter()
    engine = Hybrid(args.graph, args.cache, 'BAAI/bge-m3', args.exom, args.offline)
    engine.load()
    load_s = time.perf_counter() - start
    for q in queries:
        if not q['expected'] or not set(q['expected']) <= set(engine.names):
            p.error('expected sources must exist in graph')
    questions = [q['query'] for q in queries] + negative
    start = time.perf_counter()
    hybrid = engine.search_many(questions)
    batched_s = time.perf_counter() - start
    start = time.perf_counter()
    repeated = engine.search_many(questions)
    repeat_s = time.perf_counter() - start
    native, latencies = [], []
    for question in questions:
        start = time.perf_counter()
        rows = json.loads(subprocess.run([args.exom, 'recall', '--graph', str(args.graph),
                                          '--query', question, '--topk', '5', '--json'],
                                         capture_output=True, text=True, check=True).stdout)['results']
        latencies.append((time.perf_counter() - start) * 1000)
        native.append([r['path'] for r in rows])
    hranks = [[r['path'] for r in rows] for rows in hybrid]
    summary = {}
    for name, rankings in [('native', native), ('hybrid', hranks)]:
        summary[name] = metrics(rankings[:len(queries)], queries)
        summary[name]['categories'] = {}
        for cat in sorted({q.get('category', 'other') for q in queries}):
            ids = [i for i, q in enumerate(queries) if q.get('category', 'other') == cat]
            summary[name]['categories'][cat] = metrics([rankings[i] for i in ids], [queries[i] for i in ids])
    # Per-fact regressions, not only aggregate wins. These records remain private.
    examples = []
    for i, q in enumerate(queries):
        def first_correct(ranking):
            return next((j + 1 for j, name in enumerate(ranking) if name in q['expected']), None)
        examples.append(dict(query=q['query'], native_rank=first_correct(native[i]),
                             hybrid_rank=first_correct(hranks[i]), native=native[i], hybrid=hranks[i]))
    # Literal-anchor evidence availability, no QA correctness claim.
    anchor_checks = []
    for q, rows in zip(queries, hybrid):
        anchors = [a for group in q.get('anchors', {}).values() for a in group]
        if anchors:
            context = engine.context(q['query'], rows, 3000).casefold()
            anchor_checks.append(all(a.casefold() in context for a in anchors))
    # Reject stale cache in the executable load path without mutating user's cache.
    digest = engine.digest
    engine.digest = 'intentionally-stale'
    stale_rejected = False
    try:
        engine.load()
    except ValueError:
        stale_rejected = True
    engine.digest = digest
    assert stale_rejected
    assert engine.search_many([''])[0] == []
    report = dict(notes=len(engine.names), queries=len(queries), negative_queries=len(negative),
                  fingerprint=engine.digest, summary=summary, repeated_rankings_equal=hybrid == repeated,
                  stale_cache_rejected=stale_rejected,
                  literal_anchor_coverage_3000_chars=(statistics.mean(anchor_checks) if anchor_checks else None),
                  timing=dict(model_and_cache_load_s=load_s, batched_queries_s=batched_s,
                              repeat_batched_queries_s=repeat_s,
                              native_cli_median_ms=statistics.median(latencies)),
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  cache_bytes=args.cache.stat().st_size,
                  negative_return_counts=[dict(query=q, native=len(n), hybrid=len(h))
                                          for q, n, h in zip(negative, native[len(queries):], hybrid[len(queries):])],
                  examples=examples)
    write_report(args.output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ['examples', 'negative_return_counts']}, indent=2))


if __name__ == '__main__':
    main()
