# Zero-Mem-inspired retrieval experiment

This is a small offline prototype, **not Zero-Mem**, and does not change ExoMind's production recall. No packages, network services, credentials, or private vault contents are required.

## Reproduce

From the repository root:

```sh
cargo build --release --locked
python3 scripts/benchmark_zero_mem.py --output 30_Resources/Schemas/zero-mem-results.json
cargo test --locked
```

The Python command first runs assert-based checks for ranking, no-match/empty queries, empty corpora, evidence line provenance, and multi-evidence metrics. Temporary corpus/index files are automatically removed.

Files:

- `scripts/benchmark_zero_mem.py`: prototype and comparison runner.
- `30_Resources/Schemas/zero-mem-fixture.json`: hand-authored corpus and labels.
- `30_Resources/Schemas/zero-mem-results.json`: observed rankings, metrics, source-local evidence, and timings.

## What is implemented

- Original paragraphs preserved with source path and line ranges.
- BM25 at paragraph and note levels; weighted score fusion is a minimal hierarchy approximation, not episode/window coarse-to-fine retrieval.
- Entity/context bipartite graph from capitalized single words, plus adjacent paragraphs within the same note.
- Query-seeded Personalized PageRank, fused with lexical hierarchy scores. A small English temporal-cue heuristic changes graph weight.
- Verbatim neighboring paragraphs attached to each selected source.
- BM25/hierarchy-only ablation to distinguish lexical gains from graph gains.

Not implemented: BGE-M3/dense embeddings, actual NER, sessions/episodes, temporal validity filtering, semantic contradiction detection, reader LLM, answer calibration, or QA F1. Neighbor closure is attached evidence only and is not scored by this note-level benchmark. Capitalization can connect unrelated entities; no alias resolution is attempted. Both variants deliberately use the current ExoMind ASCII tokenizer to avoid attributing a tokenizer change to retrieval architecture.

## Protocol and observed results

The same 28 synthetic Markdown notes and 24 labeled questions are supplied to both implementations. Native ExoMind is indexed with its real CLI and ranked with its existing default weights. The inspired system deduplicates paragraph results by source note. Top-k counts source slots, not equivalent token budgets; native ghost results consume slots. No real user notes are read.

Labels include 6 lexical, 5 temporal, 4 multi-hop, 4 paraphrase, and 5 multilingual questions. Multi-hop labels require both supporting notes. **Hit@k** requires at least one expected note; **all-evidence@k** requires every expected note. MRR@5 is reciprocal rank of the first correct source, zero on a miss.

| Metric | ExoMind | BM25 + hierarchy | Inspired + graph |
|---|---:|---:|---:|
| Hit@1 | 16/24 (66.7%) | 16/24 (66.7%) | 16/24 (66.7%) |
| Hit@3 | 22/24 (91.7%) | 23/24 (95.8%) | 23/24 (95.8%) |
| Hit@5 | 23/24 (95.8%) | 23/24 (95.8%) | 23/24 (95.8%) |
| All-evidence@5 | 22/24 (91.7%) | 22/24 (91.7%) | 23/24 (95.8%) |
| Multi-hop all-evidence@5 | 3/4 | 3/4 | 4/4 |
| MRR@5 | 0.8021 | 0.8125 | 0.8125 |

Counterexamples matter: paraphrase Hit@1 falls from 2/4 to 1/4. The January Atlas incident question also loses first place. Multilingual Hit@1 remains 2/5 for all variants. No weights were tuned after observing these results.

Observed timings for the stored run: native ranking mean 0.054 ms, hierarchy-only median query 1.017 ms, inspired median query 1.977 ms. These are **not directly comparable algorithmic speed measurements**: Rust ranks precomputed TF-IDF while Python rebuilds BM25 statistics on each query, timing aggregates differ, and process/graph-load costs are excluded from native ranking. Python queries run five times and use the per-query median; native benchmark runs each query once. Neither includes QA generation.

## Interpretation and limits

Most measured gains appear without graph propagation. The graph adds one complete multi-hop retrieval at top-5, not a general first-result improvement. This does not justify replacing native recall yet.

This is a deliberately small, hand-authored diagnostic fixture made alongside the prototype, **not a held-out benchmark**, independent evaluation, or statistical evidence of superiority. There are no confidence intervals or official LoCoMo/HotpotQA results. Note-level temporal hits do not prove selection of the correct historical fact inside that note. More or larger attached evidence can consume more reader context; this experiment does not measure that cost.

Next useful validation was conducted on a real vault with adopted native changes documented in [Recall evaluation](recall-evaluation.md).
