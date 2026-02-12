#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .cli import doctor_report, index_graph_data, recall_from_graph


TOOLS = [
    {
        "name": "exom_index",
        "description": "Index notes into ExoMind graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notes_root": {"type": "string"},
                "out_root": {"type": "string", "default": ".neural"},
            },
            "required": ["notes_root"],
        },
    },
    {
        "name": "exom_recall",
        "description": "Recall top related notes from graph",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "topk": {"type": "integer", "default": 10},
                "graph": {"type": "string", "default": ".neural/graph.json"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "exom_doctor",
        "description": "Run runtime checks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "notes_root": {"type": "string", "default": "."},
                "graph": {"type": "string", "default": ".neural/graph.json"},
            },
        },
    },
]


def _ok(id_: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _tool_text(payload: Any) -> list[dict]:
    return [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}]


def handle(method: str, params: dict, id_: Any) -> dict:
    try:
        if method == "initialize":
            return _ok(
                id_,
                {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": "exom-mcp", "version": "0.1.0"},
                    "capabilities": {"tools": {}},
                },
            )

        if method == "tools/list":
            return _ok(id_, {"tools": TOOLS})

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments", {}) or {}

            if name == "exom_index":
                notes_root = Path(arguments["notes_root"]).expanduser().resolve()
                out_root = Path(arguments.get("out_root", ".neural")).expanduser().resolve()
                result = index_graph_data(notes_root, out_root)
                return _ok(id_, {"content": _tool_text(result)})

            if name == "exom_recall":
                graph = Path(arguments.get("graph", ".neural/graph.json")).expanduser().resolve()
                if not graph.exists():
                    raise FileNotFoundError(f"Graph not found: {graph}")
                g = json.loads(graph.read_text(encoding="utf-8"))
                rows = recall_from_graph(g, arguments["query"], int(arguments.get("topk", 10)))
                return _ok(id_, {"content": _tool_text({"results": rows})})

            if name == "exom_doctor":
                notes_root = Path(arguments.get("notes_root", ".")).expanduser().resolve()
                graph = Path(arguments.get("graph", ".neural/graph.json")).expanduser().resolve()
                report = doctor_report(notes_root, graph)
                return _ok(id_, {"content": _tool_text(report)})

            return _err(id_, -32602, f"Unknown tool: {name}")

        if method == "notifications/initialized":
            return {}

        return _err(id_, -32601, f"Method not found: {method}")

    except Exception as e:
        return _err(id_, -32000, str(e))


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            params = req.get("params", {})
            id_ = req.get("id")
            resp = handle(method, params, id_)
            if resp:
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps(_err(None, -32700, f"Parse error: {e}"), ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
