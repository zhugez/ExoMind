#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / ".neural" / "graph.json"
TOKEN = re.compile(r"[a-zA-Z0-9_\-]+")


def tok(s: str):
    return [x.lower() for x in TOKEN.findall(s or "")]


def load_graph():
    if not GRAPH.exists():
        raise SystemExit("Run: python scripts/index_notes.py first")
    return json.loads(GRAPH.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--topk", type=int, default=10)
    args = ap.parse_args()

    g = load_graph()
    q = set(tok(args.query))
    nodes = g["nodes"]
    edges = g["edges"]

    indeg = {}
    for e in edges:
        indeg[e["dst"]] = indeg.get(e["dst"], 0) + 1

    scored = []
    for n in nodes:
        text = f"{n.get('title','')} {n.get('path','') or ''}"
        t = set(tok(text))
        overlap = len(q & t)
        score = overlap * 2 + min(indeg.get(n["id"], 0), 10) * 0.1
        if score > 0:
            scored.append((score, n))

    scored.sort(key=lambda x: x[0], reverse=True)
    for i, (s, n) in enumerate(scored[: args.topk], 1):
        print(f"{i:02d}. score={s:.2f} | {n['title']} | {n.get('path')}")


if __name__ == "__main__":
    main()
