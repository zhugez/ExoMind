use anyhow::{Context, Result};
use chrono::{DateTime, Duration, NaiveDate, Utc};
use clap::{Parser, Subcommand, ValueEnum};
use once_cell::sync::Lazy;
use regex::Regex;
use serde::{Deserialize, Serialize};
use serde_json;
use serde_yaml;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::env;
use std::fmt;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::time::{Duration as StdDuration, Instant, SystemTime};
use walkdir::WalkDir;

const NOTE_DIRS: &[&str] = &[
    "00_Inbox",
    "10_Projects",
    "20_Areas",
    "30_Resources",
    "99_Archives",
];

const INBOX_DIR: &str = "00_Inbox";
const ARCHIVE_INBOX_DIR: &str = "99_Archives/Inbox";
const CONSOLIDATED_PREFIX: &str = "consolidated";
const METADATA_PREFIX: &str = "<!-- lifecycle";
const DECAY_THRESHOLD_DAYS: u64 = 7;
const CONSOLIDATE_LOOKBACK_DAYS: u64 = 7;

static TOKEN_REGEX: Lazy<Regex> = Lazy::new(|| Regex::new(r"[A-Za-z0-9_-]+").unwrap());
static WIKILINK_REGEX: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]").unwrap());

static RELATION_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(
        r"REL:([A-Za-z0-9_]+)\((?P<from>.+?)\s*->\s*(?P<to>.+?)\)\[(?P<confidence>[0-9.]+)\]",
    )
    .unwrap()
});

#[derive(Parser)]
#[command(name = "exom", version = env!("CARGO_PKG_VERSION"), about = "Rust-first ExoMind runtime")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Initialize the opinionated workspace layout and neural cache folders
    Init {
        #[arg(long, default_value = ".")]
        path: PathBuf,
    },
    /// Index notes into the graph cache
    Index {
        #[arg(long)]
        notes_root: PathBuf,
        #[arg(long, default_value = ".neural")]
        out_root: PathBuf,
    },
    /// Capture quick notes with relation extraction
    Capture {
        #[arg(long)]
        input: Option<String>,
        #[arg(long)]
        file: Option<PathBuf>,
        #[arg(long)]
        out_note: Option<PathBuf>,
        #[arg(long, default_value = ".")]
        notes_root: PathBuf,
        #[arg(long, default_value_t = false)]
        json: bool,
    },
    /// Recall context from an existing graph
    Recall {
        #[arg(long)]
        query: String,
        #[arg(long, default_value = "10")]
        topk: usize,
        #[arg(long, default_value = ".neural/graph.json")]
        graph: PathBuf,
        #[arg(long, default_value = "1.0")]
        lexical_weight: f64,
        #[arg(long, default_value = "1.0")]
        graph_weight: f64,
        #[arg(long, default_value = "1.0")]
        semantic_weight: f64,
        #[arg(long, default_value_t = false)]
        json: bool,
    },
    /// Validate the runtime environment
    Doctor {
        #[arg(long, default_value = ".")]
        notes_root: PathBuf,
        #[arg(long, default_value = ".neural/graph.json")]
        graph: PathBuf,
        #[arg(long, default_value_t = false)]
        json: bool,
    },
    /// Run recall benchmark against a labeled dataset
    Benchmark {
        #[arg(long)]
        dataset: PathBuf,
        #[arg(long, default_value = ".neural/graph.json")]
        graph: PathBuf,
        #[arg(long)]
        topk: usize,
        #[arg(long, default_value_t = false)]
        json: bool,
    },
    /// Manage lifecycle states for inbox notes
    Lifecycle {
        #[arg(long, default_value_t = LifecycleMode::Consolidate)]
        mode: LifecycleMode,
        #[arg(long, default_value_t = 30)]
        older_than_days: u64,
        #[arg(long, default_value = ".")]
        notes_root: PathBuf,
        #[arg(long, default_value_t = false)]
        json: bool,
    },
}

#[derive(Clone, ValueEnum, Serialize)]
#[serde(rename_all = "lowercase")]
enum LifecycleMode {
    Decay,
    Consolidate,
    Archive,
}

impl fmt::Display for LifecycleMode {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let label = match self {
            LifecycleMode::Decay => "decay",
            LifecycleMode::Consolidate => "consolidate",
            LifecycleMode::Archive => "archive",
        };
        write!(f, "{}", label)
    }
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Init { path } => {
            let root = normalize_path(path);
            init_workflow(&root)?;
            println!("INIT_OK {}", root.display());
        }
        Commands::Index {
            notes_root,
            out_root,
        } => {
            let notes_root = normalize_path(notes_root);
            let out_root = normalize_path(out_root);
            let result = index_graph_data(&notes_root, &out_root)?;
            println!(
                "INDEX_OK notes={} nodes={} edges={} -> {}",
                result.notes,
                result.nodes,
                result.edges,
                result.graph_path.display()
            );
        }
        Commands::Capture {
            input,
            file,
            out_note,
            notes_root,
            json,
        } => {
            let notes_root = normalize_path(notes_root);
            ensure_workflow_dirs(&notes_root)?;
            let source = capture_input_text(input, file)?;
            let target = resolve_capture_note(&notes_root, out_note);
            let report = run_capture(&notes_root, &target, &source)?;
            if json {
                print_json(&report)?;
            } else {
                println!(
                    "CAPTURE_OK note={} relations={}",
                    report.note, report.relation_count
                );
                for relation in &report.relations {
                    println!(
                        "  - {}({} -> {}) [{:.2}]",
                        relation.rel_type, relation.from, relation.to, relation.confidence
                    );
                }
            }
        }
        Commands::Recall {
            query,
            topk,
            graph,
            lexical_weight,
            graph_weight,
            semantic_weight,
            json,
        } => {
            let graph_path = normalize_path(graph);
            if !graph_path.exists() {
                anyhow::bail!(
                    "Graph not found: {}. Run `exom index` first.",
                    graph_path.display()
                );
            }
            let graph_data = load_graph(&graph_path)?;
            let weights = RecallWeights {
                lexical: lexical_weight,
                graph: graph_weight,
                semantic: semantic_weight,
            };
            let rows = recall_from_graph(&graph_data, &query, topk, &weights);
            if json {
                print_json(&RecallResponse {
                    query,
                    top_k: topk,
                    results: rows,
                })?;
            } else {
                for row in &rows {
                    println!(
                        "{:02}. score={:.2} | {} | {}",
                        row.rank,
                        row.score,
                        row.title,
                        row.path.as_deref().unwrap_or("None")
                    );
                }
            }
        }
        Commands::Doctor {
            notes_root,
            graph,
            json,
        } => {
            let notes_root = normalize_path(notes_root);
            let graph_path = normalize_path(graph);
            let report = doctor_report(&notes_root, &graph_path);
            if json {
                print_json(&report)?;
            } else {
                for check in &report.checks {
                    println!(
                        "{} | {} | {}",
                        if check.ok { "OK" } else { "WARN" },
                        check.name,
                        check.info
                    );
                }
                println!(
                    "{}",
                    if report.ok {
                        "DOCTOR_OK"
                    } else {
                        "DOCTOR_WARN"
                    }
                );
            }
        }
        Commands::Benchmark {
            dataset,
            graph,
            topk,
            json,
        } => {
            let graph_path = normalize_path(graph);
            if !graph_path.exists() {
                anyhow::bail!(
                    "Graph not found: {}. Run `exom index` first.",
                    graph_path.display()
                );
            }
            let dataset_path = normalize_path(dataset);
            let graph_data = load_graph(&graph_path)?;
            let dataset_file = fs::read_to_string(&dataset_path)
                .with_context(|| format!("failed to read dataset {}", dataset_path.display()))?;
            let queries: Vec<BenchmarkQuery> = serde_json::from_str(&dataset_file)
                .with_context(|| format!("failed to parse dataset {}", dataset_path.display()))?;
            let report = run_benchmark(&graph_data, &queries, topk)?;
            if json {
                print_json(&report)?;
            } else {
                println!("hit@1: {:.3}", report.hit_at_1);
                println!("hit@3: {:.3}", report.hit_at_3);
                println!("hit@5: {:.3}", report.hit_at_5);
                println!("avg latency ms: {:.3}", report.avg_latency_ms);
                println!("per-query summary:");
                for (idx, summary) in report.queries.iter().enumerate() {
                    let hit_info = summary
                        .hit_rank
                        .map(|rank| format!("rank {}", rank))
                        .unwrap_or_else(|| "MISS".to_string());
                    let target = summary.hit_path.as_deref().unwrap_or("no hit within topk");
                    println!(
                        "{:02}. {} | {} | latency={:.2}ms | {}",
                        idx + 1,
                        summary.query,
                        hit_info,
                        summary.latency_ms,
                        target
                    );
                }
            }
        }
        Commands::Lifecycle {
            mode,
            older_than_days,
            notes_root,
            json,
        } => {
            let notes_root = normalize_path(notes_root);
            ensure_workflow_dirs(&notes_root)?;
            let report = run_lifecycle(&notes_root, mode, older_than_days)?;
            if json {
                print_json(&report)?;
            } else {
                println!(
                    "LIFECYCLE {} processed={} affected={}",
                    report.mode, report.processed, report.touched
                );
                if let Some(target) = &report.summary_path {
                    println!("  summary: {}", target);
                }
                for detail in &report.details {
                    println!("  {}", detail);
                }
            }
        }
    }

    Ok(())
}

fn normalize_path(path: PathBuf) -> PathBuf {
    if path.is_absolute() {
        path
    } else {
        env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(path)
    }
}

fn init_workflow(root: &Path) -> Result<()> {
    let extras = [".neural/cache", ".neural/exports"];
    for dir in NOTE_DIRS.iter().chain(extras.iter()) {
        let target = root.join(dir);
        fs::create_dir_all(&target)
            .with_context(|| format!("failed to create directory {:?}", target))?;
    }
    Ok(())
}

fn collect_notes(notes_root: &Path) -> Result<Vec<PathBuf>> {
    let mut notes = Vec::new();
    for dir in NOTE_DIRS {
        let target = notes_root.join(dir);
        if !target.exists() {
            continue;
        }
        for entry in WalkDir::new(&target)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.file_type().is_file())
        {
            if entry
                .path()
                .extension()
                .map(|ext| ext.eq_ignore_ascii_case("md"))
                .unwrap_or(false)
            {
                notes.push(entry.into_path());
            }
        }
    }
    Ok(notes)
}

fn relative_note_id(note: &Path, base: &Path) -> Result<String> {
    let rel = note
        .strip_prefix(base)
        .with_context(|| format!("{} is not inside {}", note.display(), base.display()))?;
    Ok(rel
        .iter()
        .map(|os| os.to_string_lossy())
        .collect::<Vec<_>>()
        .join("/"))
}

fn title_from_file(path: &Path) -> Result<String> {
    let data = fs::read_to_string(path).unwrap_or_default();
    for line in data.lines() {
        if let Some(rest) = line.strip_prefix("# ") {
            return Ok(rest.trim().to_string());
        }
    }
    Ok(path
        .file_stem()
        .map(|stem| stem.to_string_lossy().to_string())
        .unwrap_or_else(|| path.display().to_string()))
}

#[derive(Clone, Serialize, Deserialize)]
struct Node {
    id: String,
    path: Option<String>,
    title: String,
    stem: String,
    #[serde(default)]
    semantic: BTreeMap<String, f64>,
}

#[derive(Serialize, Deserialize)]
struct Edge {
    src: String,
    dst: String,
    #[serde(rename = "type")]
    kind: String,
}

#[derive(Serialize, Deserialize)]
struct Stats {
    notes: usize,
    nodes: usize,
    edges: usize,
}

#[derive(Serialize, Deserialize)]
struct GraphData {
    notes_root: String,
    nodes: Vec<Node>,
    edges: Vec<Edge>,
    stats: Stats,
}

struct IndexResult {
    graph_path: PathBuf,
    notes: usize,
    nodes: usize,
    edges: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
struct TypedRelation {
    #[serde(rename = "type")]
    rel_type: String,
    from: String,
    to: String,
    confidence: f64,
}

#[derive(Serialize)]
struct CaptureReport {
    note: String,
    appended_at: String,
    relation_count: usize,
    relations: Vec<TypedRelation>,
}

#[derive(Serialize)]
struct RecallResponse {
    query: String,
    top_k: usize,
    results: Vec<RecallRow>,
}

#[derive(Serialize)]
struct LifecycleReport {
    mode: LifecycleMode,
    processed: usize,
    touched: usize,
    details: Vec<String>,
    summary_path: Option<String>,
}

#[derive(Deserialize)]
struct BenchmarkQuery {
    query: String,
    expected: Vec<String>,
}

#[derive(Serialize)]
struct BenchmarkReport {
    hit_at_1: f64,
    hit_at_3: f64,
    hit_at_5: f64,
    avg_latency_ms: f64,
    queries: Vec<QuerySummary>,
}

#[derive(Serialize)]
struct QuerySummary {
    query: String,
    hit_rank: Option<usize>,
    hit_path: Option<String>,
    latency_ms: f64,
}

fn index_graph_data(notes_root: &Path, out_root: &Path) -> Result<IndexResult> {
    struct NoteEntry {
        id: String,
        title: String,
        stem: String,
        content: String,
    }

    let notes = collect_notes(notes_root)?;
    let mut id_by_stem: HashMap<String, Vec<String>> = HashMap::new();
    let mut node_map: BTreeMap<String, Node> = BTreeMap::new();
    let mut entries = Vec::new();

    for note in &notes {
        let id = relative_note_id(note, notes_root)?;
        let stem = note
            .file_stem()
            .map(|stem| stem.to_string_lossy().to_string())
            .unwrap_or_default();
        let title = title_from_file(note)?;
        let content = fs::read_to_string(note).unwrap_or_default();
        entries.push(NoteEntry {
            id: id.clone(),
            title: title.clone(),
            stem: stem.clone(),
            content,
        });
        node_map.insert(
            id.clone(),
            Node {
                id: id.clone(),
                path: Some(id.clone()),
                title,
                stem: stem.clone(),
                semantic: BTreeMap::new(),
            },
        );
        id_by_stem.entry(stem.to_lowercase()).or_default().push(id);
    }

    let mut edges = Vec::new();
    for entry in &entries {
        for link in WIKILINK_REGEX.captures_iter(&entry.content) {
            let raw = link.get(1).map(|m| m.as_str().trim()).unwrap_or("");
            let key = Path::new(raw)
                .file_name()
                .map(|s| s.to_string_lossy().to_lowercase())
                .unwrap_or_else(|| raw.to_lowercase());
            if let Some(candidates) = id_by_stem.get(&key) {
                for dst in candidates {
                    edges.push(Edge {
                        src: entry.id.clone(),
                        dst: dst.clone(),
                        kind: "WIKILINK".into(),
                    });
                }
            } else {
                let ghost = format!("ghost/{}", raw);
                node_map.entry(ghost.clone()).or_insert_with(|| Node {
                    id: ghost.clone(),
                    path: None,
                    title: raw.to_string(),
                    stem: raw.to_string(),
                    semantic: BTreeMap::new(),
                });
                edges.push(Edge {
                    src: entry.id.clone(),
                    dst: ghost,
                    kind: "UNRESOLVED_LINK".into(),
                });
            }
        }
    }

    let mut doc_token_counts: HashMap<String, HashMap<String, usize>> = HashMap::new();
    for entry in &entries {
        let corpus = format!("{} {}", entry.title, entry.content);
        let counts = token_counts(&corpus);
        doc_token_counts.insert(entry.id.clone(), counts);
    }

    let total_docs = entries.len().max(1);
    let mut doc_freq: HashMap<String, usize> = HashMap::new();
    for counts in doc_token_counts.values() {
        for token in counts.keys() {
            *doc_freq.entry(token.clone()).or_default() += 1;
        }
    }

    for entry in &entries {
        if let Some(counts) = doc_token_counts.get(&entry.id) {
            let mut tfidf = BTreeMap::new();
            for (token, count) in counts {
                let df = *doc_freq.get(token).unwrap_or(&0) as f64;
                let idf = ((total_docs as f64 + 1.0) / (df + 1.0)).ln() + 1.0;
                tfidf.insert(token.clone(), (*count as f64) * idf);
            }
            if let Some(node) = node_map.get_mut(&entry.id) {
                node.semantic = tfidf;
            }
        }
    }

    let edges_count = edges.len();
    let graph = GraphData {
        notes_root: notes_root.display().to_string(),
        nodes: node_map.values().cloned().collect(),
        edges,
        stats: Stats {
            notes: notes.len(),
            nodes: node_map.len(),
            edges: edges_count,
        },
    };

    let graph_path = out_root.join("graph.json");
    if let Some(parent) = graph_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&graph_path, serde_json::to_string_pretty(&graph)?)?;

    Ok(IndexResult {
        graph_path,
        notes: graph.stats.notes,
        nodes: graph.stats.nodes,
        edges: graph.stats.edges,
    })
}

fn load_graph(graph_path: &Path) -> Result<GraphData> {
    let data = fs::read_to_string(graph_path)?;
    let graph: GraphData = serde_json::from_str(&data)?;
    Ok(graph)
}

#[derive(Serialize)]
struct RecallRow {
    rank: usize,
    score: f64,
    title: String,
    path: Option<String>,
}

struct RecallWeights {
    lexical: f64,
    graph: f64,
    semantic: f64,
}

fn recall_from_graph(
    graph: &GraphData,
    query: &str,
    topk: usize,
    weights: &RecallWeights,
) -> Vec<RecallRow> {
    let query_tokens = tokens(query);
    let query_counts = token_counts(query);
    let mut indegree: HashMap<&str, usize> = HashMap::new();
    for edge in &graph.edges {
        *indegree.entry(edge.dst.as_str()).or_default() += 1;
    }

    let mut scored = Vec::new();
    for node in &graph.nodes {
        let text = format!("{} {}", node.title, node.path.as_deref().unwrap_or(""));
        let lexical = lexical_overlap_score(&query_tokens, &text);
        let graph_value = graph_influence(indegree.get(node.id.as_str()).copied().unwrap_or(0));
        let semantic = semantic_score(&query_counts, &node.semantic);
        let score =
            weights.lexical * lexical + weights.graph * graph_value + weights.semantic * semantic;
        if score <= 0.0 {
            continue;
        }
        scored.push(RecallRow {
            rank: 0,
            score,
            title: node.title.clone(),
            path: node.path.clone(),
        });
    }

    scored.sort_by(|a, b| {
        b.score
            .partial_cmp(&a.score)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    scored.truncate(topk);
    for (idx, row) in scored.iter_mut().enumerate() {
        row.rank = idx + 1;
    }
    scored
}

fn token_counts(text: &str) -> HashMap<String, usize> {
    let mut counts = HashMap::new();
    for token in TOKEN_REGEX.find_iter(text) {
        let normalized = token.as_str().to_lowercase();
        *counts.entry(normalized).or_default() += 1;
    }
    counts
}

fn tokens(text: &str) -> HashSet<String> {
    token_counts(text)
        .into_iter()
        .map(|(token, _)| token)
        .collect()
}

fn lexical_overlap_score(query_tokens: &HashSet<String>, text: &str) -> f64 {
    let node_tokens = tokens(text);
    (query_tokens.intersection(&node_tokens).count() * 2) as f64
}

fn graph_influence(indegree: usize) -> f64 {
    (indegree.min(10) as f64) * 0.1
}

fn semantic_score(query_counts: &HashMap<String, usize>, vector: &BTreeMap<String, f64>) -> f64 {
    query_counts
        .iter()
        .map(|(token, count)| vector.get(token).copied().unwrap_or(0.0) * (*count as f64))
        .sum()
}

fn run_benchmark(
    graph: &GraphData,
    dataset: &[BenchmarkQuery],
    topk: usize,
) -> Result<BenchmarkReport> {
    let weights = RecallWeights {
        lexical: 1.0,
        graph: 1.0,
        semantic: 1.0,
    };
    let mut total_latency = 0.0;
    let mut hit1 = 0;
    let mut hit3 = 0;
    let mut hit5 = 0;
    let mut queries = Vec::new();

    for entry in dataset {
        let expected: HashSet<String> = entry.expected.iter().cloned().collect();
        let start = Instant::now();
        let rows = recall_from_graph(graph, &entry.query, topk, &weights);
        let latency_ms = start.elapsed().as_secs_f64() * 1000.0;
        total_latency += latency_ms;
        let mut hit_rank = None;
        let mut hit_path = None;
        for (idx, row) in rows.iter().enumerate() {
            let matched = row
                .path
                .as_deref()
                .map(|p| expected.contains(p))
                .unwrap_or(false)
                || expected.contains(&row.title);
            if matched {
                hit_rank = Some(idx + 1);
                hit_path = row.path.clone().or_else(|| Some(row.title.clone()));
                break;
            }
        }
        if let Some(rank) = hit_rank {
            if rank <= 1 {
                hit1 += 1;
            }
            if rank <= 3 {
                hit3 += 1;
            }
            if rank <= 5 {
                hit5 += 1;
            }
        }
        queries.push(QuerySummary {
            query: entry.query.clone(),
            hit_rank,
            hit_path,
            latency_ms,
        });
    }

    let total = dataset.len() as f64;
    let report = BenchmarkReport {
        hit_at_1: if total > 0.0 {
            hit1 as f64 / total
        } else {
            0.0
        },
        hit_at_3: if total > 0.0 {
            hit3 as f64 / total
        } else {
            0.0
        },
        hit_at_5: if total > 0.0 {
            hit5 as f64 / total
        } else {
            0.0
        },
        avg_latency_ms: if total > 0.0 {
            total_latency / total
        } else {
            0.0
        },
        queries,
    };
    Ok(report)
}

#[derive(Serialize)]
struct DoctorReport {
    ok: bool,
    checks: Vec<CheckResult>,
}

#[derive(Serialize)]
struct CheckResult {
    name: &'static str,
    ok: bool,
    info: String,
}

fn doctor_report(notes_root: &Path, graph_path: &Path) -> DoctorReport {
    let mut checks = Vec::new();
    let notes_root_exists = notes_root.exists();
    checks.push(CheckResult {
        name: "notes_root_exists",
        ok: notes_root_exists,
        info: notes_root.display().to_string(),
    });

    let markdown_count = if notes_root_exists {
        NOTE_DIRS
            .iter()
            .map(|dir| notes_root.join(dir))
            .filter(|dir| dir.exists())
            .map(|dir| {
                WalkDir::new(dir)
                    .into_iter()
                    .filter_map(|entry| entry.ok())
                    .filter(|entry| entry.file_type().is_file())
                    .filter(|entry| {
                        entry
                            .path()
                            .extension()
                            .map(|ext| ext.eq_ignore_ascii_case("md"))
                            .unwrap_or(false)
                    })
                    .count()
            })
            .sum()
    } else {
        0
    };

    checks.push(CheckResult {
        name: "markdown_notes_detected",
        ok: markdown_count > 0,
        info: format!("count={}", markdown_count),
    });

    let graph_exists = graph_path.exists();
    checks.push(CheckResult {
        name: "graph_exists",
        ok: graph_exists,
        info: graph_path.display().to_string(),
    });

    let ok = checks.iter().all(|c| c.ok);
    DoctorReport { ok, checks }
}

fn ensure_workflow_dirs(root: &Path) -> Result<()> {
    init_workflow(root)
}

fn capture_input_text(input: Option<String>, file: Option<PathBuf>) -> Result<String> {
    if let Some(text) = input {
        Ok(text)
    } else if let Some(path) = file {
        let normalized = normalize_path(path);
        fs::read_to_string(&normalized)
            .with_context(|| format!("failed to read capture input {}", normalized.display()))
    } else {
        anyhow::bail!("Either --input or --file is required for capture.");
    }
}

fn resolve_capture_note(notes_root: &Path, out_note: Option<PathBuf>) -> PathBuf {
    if let Some(path) = out_note {
        if path.is_absolute() {
            path
        } else {
            notes_root.join(path)
        }
    } else {
        let date = Utc::now().date_naive();
        notes_root
            .join(INBOX_DIR)
            .join(format!("{}-auto.md", date.format("%Y-%m-%d")))
    }
}

fn run_capture(notes_root: &Path, target: &Path, input_text: &str) -> Result<CaptureReport> {
    let now = Utc::now();
    let body = input_text.trim_end();
    let relations = parse_relations(body);
    let yaml_block = build_relations_yaml(&relations)?;
    let entry = format!(
        "## Capture @{}\n\n{}\n\n```yaml\n{}\n```\n\n",
        now.format("%Y-%m-%d %H:%M:%S UTC"),
        body,
        yaml_block
    );

    if let Some(parent) = target.parent() {
        fs::create_dir_all(parent)?;
    }
    let note_exists = target.exists();
    let note_len = if note_exists {
        fs::metadata(target)?.len()
    } else {
        0
    };
    let mut file = OpenOptions::new().create(true).append(true).open(target)?;
    if note_exists && note_len > 0 {
        writeln!(file)?;
    }
    if !note_exists {
        writeln!(file, "# Auto capture\n")?;
    }
    file.write_all(entry.as_bytes())?;

    let relative =
        relative_note_id(target, notes_root).unwrap_or_else(|_| target.display().to_string());
    Ok(CaptureReport {
        note: relative,
        appended_at: now.to_rfc3339(),
        relation_count: relations.len(),
        relations,
    })
}

fn build_relations_yaml(relations: &[TypedRelation]) -> Result<String> {
    #[derive(Serialize)]
    struct Block<'a> {
        relations: &'a [TypedRelation],
    }

    let raw = serde_yaml::to_string(&Block { relations })?;
    let trimmed = raw.strip_prefix("---\n").unwrap_or(&raw);
    Ok(trimmed.trim_end_matches('\n').to_string())
}

fn parse_relations(text: &str) -> Vec<TypedRelation> {
    let mut relations = Vec::new();
    for cap in RELATION_REGEX.captures_iter(text).map(|c| c) {
        let rel_type = cap
            .get(1)
            .map(|m| m.as_str().trim())
            .unwrap_or("")
            .to_string();
        let from = cap
            .name("from")
            .map(|m| m.as_str().trim())
            .unwrap_or("")
            .to_string();
        let to = cap
            .name("to")
            .map(|m| m.as_str().trim())
            .unwrap_or("")
            .to_string();
        let confidence = cap
            .name("confidence")
            .and_then(|m| m.as_str().parse::<f64>().ok())
            .unwrap_or(0.0);
        if rel_type.is_empty() || from.is_empty() || to.is_empty() {
            continue;
        }
        relations.push(TypedRelation {
            rel_type,
            from,
            to,
            confidence,
        });
    }
    relations
}

fn print_json<T: Serialize>(value: &T) -> Result<()> {
    println!("{}", serde_json::to_string_pretty(value)?);
    Ok(())
}

fn run_lifecycle(
    notes_root: &Path,
    mode: LifecycleMode,
    older_than_days: u64,
) -> Result<LifecycleReport> {
    match mode {
        LifecycleMode::Decay => run_decay(notes_root),
        LifecycleMode::Consolidate => run_consolidate(notes_root),
        LifecycleMode::Archive => run_archive(notes_root, older_than_days),
    }
}

fn run_decay(notes_root: &Path) -> Result<LifecycleReport> {
    let notes = gather_inbox_notes(notes_root)?;
    let mut details = Vec::new();
    let now = SystemTime::now();
    for note in &notes {
        let metadata = fs::metadata(note)?;
        let modified = metadata.modified().unwrap_or(now);
        let age_days = duration_since_days(now, modified);
        if age_days >= DECAY_THRESHOLD_DAYS as f64 {
            let last_reviewed = DateTime::<Utc>::from(modified).date_naive();
            let score = compute_decay_score(age_days);
            if apply_decay_metadata(note, last_reviewed, score)? {
                details.push(format!(
                    "Marked {} decay_score={:.3}",
                    relative_note_id(note, notes_root)?,
                    score
                ));
            }
        }
    }
    Ok(LifecycleReport {
        mode: LifecycleMode::Decay,
        processed: notes.len(),
        touched: details.len(),
        details,
        summary_path: None,
    })
}

fn run_consolidate(notes_root: &Path) -> Result<LifecycleReport> {
    let notes = gather_inbox_notes(notes_root)?;
    let now = Utc::now();
    let cutoff = now - Duration::days(CONSOLIDATE_LOOKBACK_DAYS as i64);
    let mut candidates = Vec::new();
    for note in &notes {
        let metadata = fs::metadata(note)?;
        let modified = metadata.modified().unwrap_or(SystemTime::now());
        let modified_dt = DateTime::<Utc>::from(modified);
        if modified_dt < cutoff {
            let rel = relative_note_id(note, notes_root)?;
            let title = title_from_file(note)?;
            candidates.push((note.clone(), modified_dt, title, rel));
        }
    }
    candidates.sort_by(|a, b| a.0.cmp(&b.0));

    let summary_name = format!("{}-{}.md", CONSOLIDATED_PREFIX, now.format("%Y-%m"));
    let summary_path = notes_root.join("99_Archives").join(summary_name);
    let mut content = String::new();
    content.push_str(&format!(
        "# Consolidated summary for {}\nGenerated: {}\n\n## Notes older than {} days\n\n",
        now.format("%B %Y"),
        now.format("%Y-%m-%d %H:%M:%S UTC"),
        CONSOLIDATE_LOOKBACK_DAYS
    ));
    if candidates.is_empty() {
        content.push_str("No eligible inbox notes.\n");
    } else {
        for (_, modified_dt, title, rel) in &candidates {
            content.push_str(&format!(
                "- {} | {} | {}\n",
                rel,
                modified_dt.format("%Y-%m-%d %H:%M:%S UTC"),
                title
            ));
        }
    }

    if let Some(parent) = summary_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(&summary_path, content)?;
    let details = candidates
        .iter()
        .map(|(_, _, _, rel)| format!("Summarized {}", rel))
        .collect();
    Ok(LifecycleReport {
        mode: LifecycleMode::Consolidate,
        processed: notes.len(),
        touched: candidates.len(),
        details,
        summary_path: Some(summary_path.display().to_string()),
    })
}

fn run_archive(notes_root: &Path, older_than_days: u64) -> Result<LifecycleReport> {
    let notes = gather_inbox_notes(notes_root)?;
    let mut details = Vec::new();
    let now = SystemTime::now();
    let lookback_secs = older_than_days.saturating_mul(86_400);
    let cutoff = now
        .checked_sub(StdDuration::from_secs(lookback_secs))
        .unwrap_or(SystemTime::UNIX_EPOCH);
    let inbox_root = notes_root.join(INBOX_DIR);
    let archive_root = notes_root.join(ARCHIVE_INBOX_DIR);

    for note in &notes {
        let metadata = fs::metadata(note)?;
        let modified = metadata.modified().unwrap_or(now);
        if modified <= cutoff {
            let rel = relative_note_id(note, notes_root)?;
            let relative_inbox = note.strip_prefix(&inbox_root).unwrap_or(note);
            let target = archive_root.join(relative_inbox);
            if let Some(parent) = target.parent() {
                fs::create_dir_all(parent)?;
            }
            if target.exists() {
                details.push(format!("Skipped exists {}", rel));
                continue;
            }
            fs::rename(note, &target)?;
            let target_rel = relative_note_id(&target, notes_root)
                .unwrap_or_else(|_| target.display().to_string());
            details.push(format!("Moved {} -> {}", rel, target_rel));
        }
    }

    Ok(LifecycleReport {
        mode: LifecycleMode::Archive,
        processed: notes.len(),
        touched: details
            .iter()
            .filter(|line| line.starts_with("Moved"))
            .count(),
        details,
        summary_path: None,
    })
}

fn duration_since_days(now: SystemTime, earlier: SystemTime) -> f64 {
    now.duration_since(earlier)
        .unwrap_or_else(|_| StdDuration::ZERO)
        .as_secs_f64()
        / 86_400.0
}

fn compute_decay_score(days: f64) -> f64 {
    (days / 90.0).min(1.0)
}

fn apply_decay_metadata(note: &Path, last_reviewed: NaiveDate, decay_score: f64) -> Result<bool> {
    let content = fs::read_to_string(note)?;
    let new_line = format!(
        "<!-- lifecycle last_reviewed={} decay_score={:.3} -->",
        last_reviewed, decay_score
    );
    if content
        .lines()
        .rev()
        .find(|line| line.trim_start().starts_with(METADATA_PREFIX))
        .map(|line| line.trim())
        == Some(new_line.as_str())
    {
        return Ok(false);
    }

    let filtered: Vec<&str> = content
        .lines()
        .filter(|line| !line.trim_start().starts_with(METADATA_PREFIX))
        .collect();
    let mut rebuilt = filtered.join("\n");
    if !rebuilt.is_empty() {
        rebuilt.push('\n');
    }
    rebuilt.push_str(&new_line);
    rebuilt.push('\n');
    fs::write(note, rebuilt)?;
    Ok(true)
}

fn gather_inbox_notes(notes_root: &Path) -> Result<Vec<PathBuf>> {
    let mut notes = Vec::new();
    let inbox = notes_root.join(INBOX_DIR);
    if !inbox.exists() {
        return Ok(notes);
    }
    for entry in WalkDir::new(&inbox)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.file_type().is_file())
    {
        if entry
            .path()
            .extension()
            .map(|ext| ext.eq_ignore_ascii_case("md"))
            .unwrap_or(false)
        {
            notes.push(entry.into_path());
        }
    }
    notes.sort();
    Ok(notes)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tokens_split() {
        let result = tokens("Hello, WORLD-42_test!");
        assert!(result.contains("hello"));
        assert!(result.contains("world-42_test"));
    }

    #[test]
    fn token_counts_tracks_multiples() {
        let counts = token_counts("Rust rust RUST!!!");
        assert_eq!(counts.get("rust"), Some(&3));
    }

    #[test]
    fn lexical_overlap_zero_when_no_shared_tokens() {
        let query = tokens("alpha beta");
        let score = lexical_overlap_score(&query, "gamma delta");
        assert_eq!(score, 0.0);
    }

    #[test]
    fn graph_influence_caps_at_ten() {
        assert_eq!(graph_influence(5), 0.5);
        assert_eq!(graph_influence(20), 1.0);
    }

    #[test]
    fn semantic_score_considers_weights() {
        let mut vector = BTreeMap::new();
        vector.insert("foo".to_string(), 2.5);
        vector.insert("bar".to_string(), 1.0);
        let mut query_counts = HashMap::new();
        query_counts.insert("foo".to_string(), 2);
        query_counts.insert("baz".to_string(), 1);
        let score = semantic_score(&query_counts, &vector);
        assert!((score - 5.0).abs() < f64::EPSILON);
    }

    #[test]
    fn parse_typed_relations() {
        let sample =
            "REL:CAUSED_BY(API Timeout->Latency Spike)[0.82] and REL:RELATED_TO(Demo->Spec)[1]";
        let relations = parse_relations(sample);
        assert_eq!(relations.len(), 2);
        assert_eq!(relations[0].rel_type, "CAUSED_BY");
        assert_eq!(relations[0].from, "API Timeout");
        assert_eq!(relations[0].to, "Latency Spike");
        assert!((relations[0].confidence - 0.82).abs() < f64::EPSILON);
        assert_eq!(relations[1].rel_type, "RELATED_TO");
        assert_eq!(relations[1].confidence, 1.0);
    }

    #[test]
    fn compute_decay_score_bounds() {
        assert_eq!(compute_decay_score(0.0), 0.0);
        let mid = compute_decay_score(45.0);
        assert!((mid - 0.5).abs() < 1e-6);
        assert_eq!(compute_decay_score(200.0), 1.0);
    }
}
