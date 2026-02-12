from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .cli import index_graph_data, recall_from_graph

app = FastAPI(title="ExoMind Server", version="0.9.1b1")


class IndexRequest(BaseModel):
    notes_root: str
    out_root: str = ".neural"


class RecallRequest(BaseModel):
    query: str
    topk: int = 10
    graph: str = ".neural/graph.json"


@app.get("/health")
def health():
    return {"ok": True, "service": "exomind"}


@app.post("/index")
def index(req: IndexRequest):
    notes_root = Path(req.notes_root).expanduser().resolve()
    out_root = Path(req.out_root).expanduser().resolve()
    result = index_graph_data(notes_root=notes_root, out_root=out_root)
    return result


@app.post("/recall")
def recall(req: RecallRequest):
    graph = Path(req.graph).expanduser().resolve()
    if not graph.exists():
        raise HTTPException(status_code=404, detail=f"Graph not found: {graph}")
    g = json.loads(graph.read_text(encoding="utf-8"))
    rows = recall_from_graph(g, req.query, req.topk)
    return {"query": req.query, "topk": req.topk, "results": rows}
