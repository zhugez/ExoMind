# Optional local BGE-M3 hybrid recall

The default Rust CLI remains BM25-based. `scripts/exom_hybrid.py` is an explicit optional Python entry point, not automatic interception of `exom recall`, MCP, or Pi hooks. It combines native candidate ranks with BGE-M3 cosine ranks using equal reciprocal-rank fusion, constant 60. No LLM/API reader or generated summaries are used. It does not copy upstream Zero-Mem code.

## Setup and use

Run from the repository root:

```sh
cargo build --release --locked
python3 -m venv .venv-hybrid
.venv-hybrid/bin/python -m pip install -r requirements-hybrid.txt
export VAULT="$HOME/Yasna-Memory"
export CACHE="$HOME/.cache/exom-hybrid"
mkdir -p "$CACHE"
target/release/exom index --notes-root "$VAULT" --out-root "$CACHE"
.venv-hybrid/bin/python scripts/exom_hybrid.py index \
  --graph "$CACHE/graph.json" --cache "$CACHE/dense.json" --exom target/release/exom
.venv-hybrid/bin/python scripts/exom_hybrid.py recall \
  --graph "$CACHE/graph.json" --cache "$CACHE/dense.json" --exom target/release/exom \
  --offline --query 'Which Rust logging and error handling libraries are preferred?'
.venv-hybrid/bin/python scripts/exom_hybrid.py pi-context \
  --graph "$CACHE/graph.json" --cache "$CACHE/dense.json" --exom target/release/exom \
  --offline --query 'Which Rust libraries are preferred?' --max-chars 3000
```

Initial use downloads BGE-M3 model weights, not note contents. Add `--offline` to indexing too if weights already exist locally. Runtime processing is CPU-only and local. Install a suitable CPU PyTorch build if you want to avoid unnecessary CUDA packages. The dependency ranges are not an exact historical lockfile. On the tested environment a loaded process used about 2.3 GiB peak RSS; one-shot CLI calls reload the model each time. For batch jobs use `Hybrid.search_many` to amortize startup.

Cache files include private embeddings and paths; they are written atomically with private temporary-file permissions. Keep graph, cache, reports and real datasets outside the public repository. Source paths must stay inside the graph's notes root. The cache fingerprint covers graph content and current note texts, along with exact path/model matching. Changes require re-running native index and hybrid index. Cache files must not overwrite graph or source notes.

`pi-context` returns bounded verbatim query-local snippets, not the native XML wrapper. It is suitable for explicit context injection but does not automatically replace existing Pi/MCP integration. Dense retrieval returns candidates even for unsupported queries; there is no reliable answerability threshold. Empty queries return no results. RRF scores/ranks are not calibrated confidence.

## Deep real-vault diagnostic

The integrated code was measured against a freshly indexed real vault of 13 notes. This includes one additional note compared with the earlier 12-note experiments, so comparisons with upstream results from those experiments are not controlled head-to-head comparisons. There are 72 development questions, 18 additional paraphrases of known facts, and 8 unsupported probes. No weights were tuned on these runs.

| Metric | Native BM25 | Native + BGE-M3 |
|---|---:|---:|
| Development Hit@1 | 42/72 | 52/72 |
| Development all-sources@5 | 62/72 | 63/72 |
| Development MRR@5 | 0.7060 | 0.7782 |
| Fresh-paraphrase Hit@1 | 11/18 | 15/18 |
| Fresh-paraphrase all-sources@5 | 18/18 | 18/18 |

First-correct-source rank improved for 14 development questions and regressed for 5; it improved for 6 fresh paraphrases and regressed for 1. The other ranks were unchanged. Repeated top-5 rankings were identical. Stale-cache rejection and empty-query checks passed through the executable load/search interfaces.

Literal answer-anchor availability in hybrid query-local context, capped at 3000 characters, was 46/72. This is not generated answer accuracy, entailment checking, or proof of correct temporal interpretation. It is not comparable with the previous 256-word full-note diagnostic. Native and hybrid both returned sources for all 8 unsupported questions.

CPU measurements: model/cache load 7.40 seconds; batch of 80 development/unsupported queries 8.16 seconds, repeat 11.58 seconds. Batch of 18 fresh paraphrases 3.17 seconds, repeat 2.19 seconds. Native CLI median including startup was 3.57 ms on the development run. Peak process RSS was 2,401,444 KiB, embedding JSON cache 296,261 bytes. These are observed single-environment measurements, not latency percentiles or throughput guarantees; tokenizer/model libraries may use multithreading. Native corpus index/model download time was not instrumented in this run.

The corpus is small, questions are manually authored and correlated, and fresh paraphrases are not independent unseen facts. This is a deep diagnostic of this vault, **not a comprehensive generalization benchmark**. Results do not establish superiority over Zero-Mem on equal current corpora, nor QA correctness. Private artifacts remain at `~/.cache/exom-bench-real/`.

## Reproduce on your private labels

Use a JSON object with `queries`, each containing `query`, nonempty `expected` source paths and optional `category`/`anchors`, plus optional `negative` strings. Source paths are relative to the graph's notes root. Optional anchors map source paths to lists of literal answer fragments.

```sh
.venv-hybrid/bin/python scripts/benchmark_hybrid.py \
  --graph "$CACHE/graph.json" --cache "$CACHE/dense.json" \
  --queries /private/labels.json --output /private/report.json \
  --exom target/release/exom --offline
python3 -m unittest discover -s scripts -p 'test_*.py'
```

Reports contain private questions and source paths. The runner reports category metrics, per-query regressions, repeated rankings, unsupported return counts, resource use, fixed-budget context anchors and stale-cache checks. It does not invoke a QA model or automatically publish any output.
