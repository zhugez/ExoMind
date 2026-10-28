# Recall evaluation

A local diagnostic on a private real vault compared existing ExoMind, the stdlib-inspired prototype, and upstream Zero-Mem commit `e1b2f8ef98a3d023478ddb2049aba11753296d42`. No private notes, questions, source rankings, or model-generated answers are published here. All memory processing was local, using BGE-M3 and en_core_web_trf on CPU for upstream Zero-Mem; no reader/API was invoked.

The corpus contained 12 notes. The expanded evaluation contains 72 answerable queries: 22 facts each expressed in English, Vietnamese, and unaccented Vietnamese, plus 6 multi-source questions. These are correlated variants, not 72 independent facts. Eight separate unsupported questions probe negative-query behavior. Labels and literal answer anchors were fixed before running this expanded evaluation. They were authored after reading the corpus, not by an independent evaluator. The updated implementation was developed after seeing these results, so post-change results are development-set measurements, not held-out generalization evidence.

| Source ranking | Existing ExoMind | Inspired prototype | Official Zero-Mem fusion | Updated ExoMind |
|---|---:|---:|---:|---:|
| Hit@1 | 29/72 | 42/72 | 49/72 | 42/72 |
| Hit@3 | 51/72 | 56/72 | 63/72 | 62/72 |
| All expected sources @5 | 55/72 | 63/72 | 67/72 | 62/72 |
| MRR@5 | 0.556 | 0.688 | 0.782 | 0.706 |

Hit@k requires any labeled source, whereas all-sources@k requires every source for multi-source questions. Top-k counts notes, not reader tokens.

Official graph-only reached 48/72 Hit@1, compared with fusion's 49/72. The hierarchy returned no passage sources or selected turns under this original-note input format. This is an input-adaptation limitation, not evidence that hierarchy is intrinsically useless. Fusion was stable on a repeated top-5 retrieval pass. All systems returned candidates on all eight unsupported questions; returning a note does not demonstrate that the requested fact exists, and no answer/abstention claim is made.

A separate diagnostic concatenated ranked original notes and truncated to 256 whitespace words, then checked literal answer anchors with accent folding. It measures evidence availability under a fixed readout, not answer correctness or native evidence quality. Existing ExoMind reached 26/72, inspired 39/72, official fusion 42/72. Actual hierarchy/fusion selected-turn anchor coverage was zero for this input format. Note-level retrieval scores alone hide that limitation.

## Adopted changes

The native implementation adopts BM25 length normalization, Vietnamese accent folding, relevance-gated graph boosts, and query-local verbatim excerpts. It does not import upstream code or add dense models, NER, PageRank, generative summaries, or new online services. A single small Unicode normalization dependency handles composed/decomposed Vietnamese text consistently. Existing graph files remain readable, but reindexing is required to recover accented terms that the previous tokenizer discarded.

BM25 improves native length handling without the model footprint. Accent normalization addresses a directly observed weakness, but is not translation: Vietnamese questions about exclusively English facts can still miss. Graph-only boosts no longer manufacture relevance for a completely unmatched query; lexical matches on an unsupported question can still return candidates. Excerpts start at a matching line but are not semantic evidence selection or temporal contradiction detection.

The private reproducibility artifacts are stored outside this repository at `~/.cache/exom-bench-real/`, including corpus snapshots, labels, scripts, upstream results and post-change measurements. The public synthetic experiment remains reproducible with `scripts/benchmark_zero_mem.py`. Real-vault speed comparisons are intentionally omitted because implementations differ in language, encoder cost, cache state, and timed stages.
