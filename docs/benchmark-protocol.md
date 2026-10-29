# ExoMind research benchmark protocol v1

Status: adopted evaluation policy; execution infrastructure is partial. This document does not claim that the public benchmarks, independent holdout, QA evaluation or statistical gates have already run. Protocol settings below are design decisions, not measured facts. Task scope: evidence-grounded long-term memory for agents, not biological brain simulation.

## Research objective

Test whether local provenance-preserving hybrid memory improves evidence retrieval and memory-grounded answers under a fixed reader-context budget, while making update/abstention failures and operating costs explicit. BM25 plus BGE-M3 alone is an experimental baseline, not an established novel contribution. A paper needs a defensible new mechanism and evidence against strong controls.

## Selected evaluation suite

| Track | Fixed dataset choice | Role and report |
|---|---|---|
| Primary public memory | LongMemEval **cleaned S**, all official evaluation instances | Primary paper result: official QA correctness/accuracy, overall and official question types; abstention reported separately. Retrieval excludes officially unanswerable cases, following upstream. |
| Secondary public memory | LoCoMo, official `data/locomo10.json`, all conversations | External replication: upstream QA scorer, per-category results and evidence retrieval against available `dia_id` labels. Retain and identify every category, including categories an upstream scorer handles differently; never silently drop hard cases. |
| Local utility | Frozen private real-vault snapshots and real historical user queries | Multilingual, exact-code, temporal/update, multi-source and unsupported-query diagnostics. Development and independent holdout separated by fact/topic/session family. |
| Controlled lifecycle supplement | Versioned event sequences and counterfactual updates, explicitly labeled constructed data | Stale/current answer errors, as-of queries, deletion visibility and incremental index behavior. Never call constructed sequences naturally occurring real data. |

LongMemEval oracle is a diagnostic reader upper-reference, not the main memory result. LongMemEval M is a scale extension after the primary protocol works; it is not required for every candidate iteration. LoCoMo is conversational data produced through the authors' generation/annotation pipeline, not a naturally collected private-user corpus. Neither public benchmark substitutes for real-use validation. HotpotQA is not a core acceptance gate: it tests multi-hop QA rather than the full memory lifecycle.

### Sources verified for this protocol

- LongMemEval official README: https://github.com/xiaowu0162/LongMemEval . It identifies the five abilities, cleaned dataset, schema, QA/retrieval entry points and treatment of abstention queries in retrieval evaluation.
- Cleaned dataset linked by upstream: https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned . Main file: `longmemeval_s_cleaned.json`; oracle and M variants are separate.
- LoCoMo official README: https://github.com/snap-research/locomo . It specifies ten conversations, timestamp/session/turn structure, QA evidence IDs and separate generated summaries/observations.
- LoCoMo official data path: https://github.com/snap-research/locomo/blob/main/data/locomo10.json . Pin and inspect evaluator source before an official-scored run; secondary descriptions of its metrics are not authoritative.

At execution, record exact repository commits, dataset revisions/file hashes, licenses, evaluator source, filters and counts. Do not use mutable `main` as the sole provenance. Existing benchmark contamination in pretrained models cannot be excluded; disclose it.

## Data and split rules

1. Freeze corpus, labels and manifests before comparing candidates. Compare systems only on identical dataset hashes; corpus changes create a new named run, not an unmarked continuation.
2. Public benchmark evaluation instances are final evaluation data, not a convenient tuning set. Do not assume the official files provide train/dev/test partitions. Tune on separately sourced development data. If the public evaluation has already influenced a design, label it exposed and use additional held-out validation; do not retroactively call it unseen.
3. Private labels point to original evidence IDs/line spans, all acceptable alternatives, fact-family IDs, question language, category, temporal scope and answerability. Retrieval relevance can be graded only when independently labeled; otherwise use binary labels and state that limitation.
4. Group paraphrases/translations and adjacent questions about the same fact in one split. The existing 72 and 18 questions are exposed diagnostics, not an independent test set.
5. A human other than the implementing evaluator labels the new private holdout where possible. Two annotators independently label answer correctness and evidence support for the audited set; adjudicate disagreements and report raw agreement. If this is unavailable, explicitly downgrade the evidence strength.
6. Build indexes from allowable history only. Never index QA answers, evidence labels, oracle summaries, future sessions or evaluator annotations. Do not use the question to alter offline memory construction. Preserve timestamps/speakers/IDs, and isolate each benchmark history where required.
7. For an as-of query, exclude future events. Current-state questions and historical-state questions are different labels. An overwritten fact may remain valid historical evidence; deletion semantics must distinguish search exclusion from physical data erasure.

## Metrics: fixed primary and secondary endpoints

### Paper primary endpoint

**LongMemEval cleaned-S official QA accuracy**, with all official abilities reported, identical reader/prompt and **4,096 reader-token evidence budget**. This token budget is an ExoMind protocol choice, not a claim about the official benchmark default. Run the upstream QA evaluator with pinned judge/model/prompt/configuration. Disclose judge stochasticity and errors; audit a reproducibly selected sample and every system-disagreement case used in qualitative claims.

If a fixed local reader/judge is used rather than upstream's documented evaluator, label that result **local-protocol QA**, not official score. Never claim QA evaluation is complete when only retrieval ran. Reader/judge API use involving private data requires explicit authorization; default private-data inference is local.

### Optimization primary endpoint (no reader required)

**All-evidence recall under 4,096 reader tokens**, at original evidence-unit level. Score whether all required evidence groups have at least one acceptable support span represented in the final context. Also publish ordinary evidence recall so partial recovery is visible. Exclude unanswerable and missing-evidence-label cases from this metric, and publish the exclusion counts. Note-level Hit@k remains diagnostic only.

Use the same reader tokenizer, context packing/truncation rules and exact metadata accounting for all systems; paths, timestamps and source markers count toward the evidence budget. No per-system hidden extra context or free evidence closure. Evaluate budgets **1,024 / 2,048 / 4,096 / 8,192 tokens** as a quality-cost curve, with 4,096 fixed as the primary setting.

### Mandatory secondary metrics

- Evidence Recall@5/10, all-evidence@5/10, MRR@10; nDCG@10 with binary or independently annotated graded relevance. Define the ranking unit and tie policy.
- QA accuracy per official category; normalized EM/token F1 only as secondary diagnostics where appropriate. Literal substring anchors are not answer-correctness evidence.
- Citation precision: supported factual answer claims divided by factual answer claims with evaluable support. Citation completeness: supported-and-cited factual claims divided by all factual claims. Define segmentation/adjudication; do not implement it as mere filename matching.
- Answerable accuracy and unanswerable abstention recall/precision separately; false-answer rate on negative questions. A retriever returning candidates does not by itself count as a hallucinated answer.
- Selective accuracy–coverage curve and area under risk–coverage curve only if a real, dev-calibrated confidence/abstention signal exists. RRF score is not a calibrated probability. Mark not implemented otherwise.
- Knowledge-update accuracy, stale-current-answer rate and temporal/as-of accuracy, with denominators explicit. Report history visibility violations independently of generated answer accuracy.
- Per-language performance: English, Vietnamese accented/unaccented and cross-language questions; report both facts and query counts to avoid treating translations as independent facts.

## Required comparison matrix

Core baselines: native lexical/BM25, BGE-M3 dense-only, equal-RRF BM25+BGE-M3, and a verified official Zero-Mem adapter. Preserve an original ExoMind baseline artifact for historical comparison. No-memory reader and oracle-evidence reader are QA controls; they are not required in a retrieval-only iteration.

Use the same encoder/revision for dense baselines and the applicable upstream configuration for Zero-Mem. Record differences rather than making unfair equivalence claims. Zero-Mem graph/hierarchy/fusion outputs must pass adapter sanity checks: supported input schema, evidence identity mapping, chronological/session boundaries and nonempty outputs on suitable answerable fixtures. A broken/empty hierarchy marks the whole-system comparison **inconclusive**, not a valid hierarchy defeat.

Required mechanism ablations when affected: normalization on/off; BM25 vs TF-IDF; dense off/on; RRF vs the preregistered alternative; graph propagation off/on; query-local vs head-of-note excerpt. Run only meaningful configurations, and report group effects when a clean individual ablation is unavailable. No choosing fusion weights using final evaluation labels.

## Statistical analysis

Use paired comparisons on identical questions and **cluster bootstrap by conversation/history or private fact/topic family**, not independent bootstrap over paraphrases. Protocol defaults: 10,000 bootstrap replicates, seed 20261028, percentile 95% interval for the paired change in the primary metric. These are planned settings, not completed analyses.

LoCoMo has few conversation clusters; show per-conversation effects and explicitly flag uncertain bootstrap inference. For query-specific histories use the true shared-history relationship where available, not arbitrarily one cluster per paraphrase. Report wins/ties/losses and effect sizes. If a stochastic reader/judge is used, repeat the final QA comparison across three declared generation seeds when supported; record when the provider does not guarantee determinism. Multiple secondary tests are exploratory, not independent discoveries.

## Performance and operational measurements

Record machine/OS, CPU/GPU, available RAM, library versions, model revision/dtype, threads, batch size and power/cost methodology if claimed. Separate:

- model download from model load;
- cold full indexing from warm cache load and incremental update/delete;
- encoder inference, lexical retrieval, dense search, fusion, evidence packing and reader inference;
- warm single-query p50/p95/p99 from batched throughput and cold CLI startup;
- peak process RSS, GPU peak memory, index bytes and model-weight bytes.

Protocol defaults: five timing repetitions after one declared warm-up, same hardware and concurrency; publish raw timings and aggregates. Exclude warm-up explicitly, retain cold observations separately. No claims of energy efficiency without actual energy measurements. No direct speedup calculation between native rank-only latency and Python end-to-end latency.

## Candidate acceptance and release gates

A benchmark is a measurement tool, not permission to tune endlessly against held-out labels.

- Every candidate: frozen real development corpus, regression tests, retrieval/evidence metrics, negative probes and resource checks. Synthetic smoke tests supplement this, never replace it. Large public QA sweeps can be batched by checkpoint rather than invoked on every edit.
- Promote a quality candidate only if paired primary optimization-metric improvement has a 95% interval above zero on an independently held-out set. If not, label **inconclusive**, not improved. Gains on exposed development questions alone justify continued experiments, not a research claim.
- Default safety noninferiority margin: no more than 2 percentage points worse on negative false-answer rate or stale-current-answer rate, judged using a one-sided 95% paired uncertainty bound. This margin is a protocol choice and requires enough data; insufficient power means inconclusive. Never silently drop a failing category.
- Default optional-hybrid resource envelope on the declared reference machine: peak process RSS <= 4 GiB and warm single-query end-to-end p95 <= 1 second, excluding reader generation. These are target constraints, **not verified guarantees**. Native default may not acquire mandatory model downloads or Python dependencies.
- Quality/cost tradeoffs outside the envelope require an explicit documented operator decision; they are not automatically accepted because mean accuracy increased.
- Final paper checkpoint: full pinned LongMemEval cleaned-S and LoCoMo, real held-out results, QA controls, ablations, uncertainty, failure analysis and artifact manifest. No claiming full gate success while one is absent.

## Run manifest and reporting contract

Each run stores: protocol version; git/model/dataset/evaluator revisions; dataset hash; unit/adapter configuration; dev-vs-held-out status; category and exclusion counts; reader/tokenizer/prompt/judge hashes; context budget; seeds; resource configuration; raw per-query ranks/evidence/answers when permitted; paired statistics; failures; timing samples; and cost. Output format must distinguish `measured`, `not_run`, `inconclusive`, `failed` and `passed` rather than filling missing entries with zero.

Private artifacts stay outside Git. Publish aggregate metrics and public-benchmark artifacts only when licenses permit. Any change to primary endpoints, budget or acceptance margins increments protocol version before the next held-out evaluation. The present scripts are diagnostic building blocks: they do **not yet implement** official dataset adapters, token-budget evidence scoring, paired bootstrap, QA/citation evaluation or reference-machine percentile gates. Those gaps must be closed before claiming protocol-complete results.

## Implementation order

1. Add a common evidence-ID adapter and immutable run manifest; verify LongMemEval cleaned-S and LoCoMo loaders against pinned upstream schema.
2. Implement tokenizer-budget context packing, evidence-group recall, category reporting and cluster-paired bootstrap. Use current private questions only as development data.
3. Freeze an independently labeled private holdout and reference hardware/configuration. Run lexical/dense/hybrid/upstream retrieval ablations.
4. Configure one reader and judge protocol; obtain permission before external paid inference/private API use. Run official QA and controlled update/abstention evaluation.
5. Freeze the final candidate and run the full paper suite once, then report all failures and uncertainty without tuning on those final labels.
