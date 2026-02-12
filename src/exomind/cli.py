#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

TOKEN = re.compile(r"[a-zA-Z0-9_\-]+")
NOTE_DIRS = ["00_Inbox", "10_Projects", "20_Areas", "30_Resources", "99_Archives"]
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def _tok(s: str):
    return [x.lower() for x in TOKEN.findall(s or "")]


def _title_from_file(path: Path) -> str:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    for line in txt.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _collect_notes(base: Path):
    notes = []
    for d in NOTE_DIRS:
        p = base / d
        if p.exists():
            notes.extend([x for x in p.rglob("*.md") if x.is_file()])
    return notes


def index_graph_data(notes_root: Path, out_root: Path) -> dict:
    out_root.mkdir(parents=True, exist_ok=True)
    notes = _collect_notes(notes_root)

    id_by_stem = {}
    node_map = {}

    for n in notes:
        nid = str(n.relative_to(notes_root)).replace("\\", "/")
        body = n.read_text(encoding="utf-8", errors="ignore")
        node_map[nid] = {
            "id": nid,
            "path": nid,
            "title": _title_from_file(n),
            "stem": n.stem,
            "content": body[:8000],
        }
        id_by_stem.setdefault(n.stem.lower(), []).append(nid)

    edges = []
    for n in notes:
        src = str(n.relative_to(notes_root)).replace("\\", "/")
        txt = n.read_text(encoding="utf-8", errors="ignore")
        links = [m.group(1).strip() for m in WIKILINK_RE.finditer(txt)]
        for raw in links:
            key = Path(raw).name.lower()
            candidates = id_by_stem.get(key, [])
            if candidates:
                for dst in candidates:
                    edges.append({"src": src, "dst": dst, "type": "WIKILINK"})
            else:
                ghost = f"ghost/{raw}"
                if ghost not in node_map:
                    node_map[ghost] = {"id": ghost, "path": None, "title": raw, "stem": raw}
                edges.append({"src": src, "dst": ghost, "type": "UNRESOLVED_LINK"})

    graph = {
        "notes_root": str(notes_root),
        "nodes": list(node_map.values()),
        "edges": edges,
        "stats": {"notes": len(notes), "nodes": len(node_map), "edges": len(edges)},
    }

    out = out_root / "graph.json"
    out.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "graph_path": str(out),
        "notes": len(notes),
        "nodes": len(node_map),
        "edges": len(edges),
    }


def recall_from_graph(graph: dict, query: str, topk: int) -> list[dict]:
    q = set(_tok(query))
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    indeg = {}
    for e in edges:
        indeg[e["dst"]] = indeg.get(e["dst"], 0) + 1

    scored = []
    for n in nodes:
        text = f"{n.get('title','')} {n.get('path','') or ''} {n.get('content','') or ''}"
        overlap = len(q & set(_tok(text)))
        score = overlap * 2 + min(indeg.get(n["id"], 0), 10) * 0.1
        if score > 0:
            scored.append((score, n))

    scored.sort(key=lambda x: x[0], reverse=True)
    rows = []
    for i, (s, n) in enumerate(scored[:topk], 1):
        rows.append({
            "rank": i,
            "score": round(float(s), 4),
            "title": n.get("title"),
            "path": n.get("path"),
        })
    return rows


def doctor_report(notes_root: Path, graph_path: Path) -> dict:
    checks = []
    checks.append({"name": "python", "ok": True, "info": "ok"})
    checks.append({"name": "notes_root_exists", "ok": notes_root.exists(), "info": str(notes_root)})

    if notes_root.exists():
        count = 0
        for d in NOTE_DIRS:
            p = notes_root / d
            if p.exists():
                count += sum(1 for _ in p.rglob("*.md"))
        checks.append({"name": "markdown_notes_detected", "ok": count > 0, "info": f"count={count}"})
    else:
        checks.append({"name": "markdown_notes_detected", "ok": False, "info": "notes_root missing"})

    checks.append({"name": "graph_exists", "ok": graph_path.exists(), "info": str(graph_path)})
    checks.append({"name": "uvicorn_available", "ok": shutil.which("uvicorn") is not None, "info": "optional for serve"})

    ok_all = all(c["ok"] for c in checks if c["name"] != "uvicorn_available")
    return {"ok": ok_all, "checks": checks}


def cmd_init(args):
    root = Path(args.path).expanduser().resolve()
    for d in NOTE_DIRS + [".neural/cache", ".neural/exports"]:
        (root / d).mkdir(parents=True, exist_ok=True)
    print(f"INIT_OK {root}")


def cmd_index(args):
    notes_root = Path(args.notes_root).expanduser().resolve()
    out_root = Path(args.out_root).expanduser().resolve()
    result = index_graph_data(notes_root=notes_root, out_root=out_root)
    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
        return
    print(
        f"INDEX_OK notes={result['notes']} nodes={result['nodes']} edges={result['edges']} -> {result['graph_path']}"
    )


def cmd_recall(args):
    graph_path = Path(args.graph).expanduser().resolve()
    if not graph_path.exists():
        raise SystemExit(f"Graph not found: {graph_path}. Run exom index first.")

    g = json.loads(graph_path.read_text(encoding="utf-8"))
    rows = recall_from_graph(g, args.query, args.topk)
    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "query": args.query, "topk": args.topk, "rows": rows}, ensure_ascii=False))
        return
    if not rows:
        print("NO_RESULTS")
        return
    for r in rows:
        print(f"{r['rank']:02d}. score={r['score']:.2f} | {r['title']} | {r['path']}")


def cmd_doctor(args):
    notes_root = Path(args.notes_root).expanduser().resolve()
    graph_path = Path(args.graph).expanduser().resolve()
    report = doctor_report(notes_root, graph_path)

    if getattr(args, "json", False):
        print(json.dumps(report, ensure_ascii=False))
        return
    for c in report["checks"]:
        print(f"{'OK' if c['ok'] else 'WARN'} | {c['name']} | {c['info']}")
    print("DOCTOR_OK" if report["ok"] else "DOCTOR_WARN")


def cmd_serve(args):
    try:
        import uvicorn
    except Exception as e:
        raise SystemExit(
            f"uvicorn not installed ({e}). Install with: pip install exomind[server]"
        )

    uvicorn.run("exomind.server:app", host=args.host, port=args.port, reload=args.reload)


def cmd_mcp(_args):
    try:
        from .mcp_bridge import main as mcp_main
    except Exception:
        import sys
        sys.path.append(str(Path(__file__).resolve().parents[1]))
        from exomind.mcp_bridge import main as mcp_main

    mcp_main()


def build_parser():
    p = argparse.ArgumentParser(prog="exom", description="ExoMind CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="Initialize folder skeleton")
    sp.add_argument("--path", default=".")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("index", help="Index notes into graph")
    sp.add_argument("--notes-root", required=True)
    sp.add_argument("--out-root", default=".neural")
    sp.add_argument("--json", action="store_true", help="Output JSON")
    sp.set_defaults(func=cmd_index)

    sp = sub.add_parser("recall", help="Recall from graph")
    sp.add_argument("--query", required=True)
    sp.add_argument("--topk", type=int, default=10)
    sp.add_argument("--graph", default=".neural/graph.json")
    sp.add_argument("--json", action="store_true", help="Output JSON")
    sp.set_defaults(func=cmd_recall)

    sp = sub.add_parser("doctor", help="Runtime health checks")
    sp.add_argument("--notes-root", default=".")
    sp.add_argument("--graph", default=".neural/graph.json")
    sp.add_argument("--json", action="store_true", help="Output JSON")
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("serve", help="Run API server")
    sp.add_argument("--host", default="127.0.0.1")
    sp.add_argument("--port", type=int, default=8787)
    sp.add_argument("--reload", action="store_true")
    sp.set_defaults(func=cmd_serve)

    sp = sub.add_parser("mcp", help="Run MCP stdio bridge")
    sp.set_defaults(func=cmd_mcp)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
