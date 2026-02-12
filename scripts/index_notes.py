#!/usr/bin/env python3
import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTE_DIRS = ["00_Inbox", "10_Projects", "20_Areas", "30_Resources", "99_Archives"]
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")


def rel_note_id(path: Path, base: Path) -> str:
    return str(path.relative_to(base)).replace('\\', '/')


def title_from_file(path: Path) -> str:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    for line in txt.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def collect_notes(base: Path):
    notes = []
    for d in DEFAULT_NOTE_DIRS:
        p = base / d
        if not p.exists():
            continue
        notes.extend([x for x in p.rglob("*.md") if x.is_file()])
    return notes


def main():
    ap = argparse.ArgumentParser(description="Index Obsidian-style notes into ExoMind graph")
    ap.add_argument("--notes-root", default=str(ROOT), help="Path to real notes vault (default: this repo)")
    args = ap.parse_args()

    notes_root = Path(args.notes_root).expanduser().resolve()
    notes = collect_notes(notes_root)

    id_by_stem = {}
    node_map = {}

    for n in notes:
        nid = rel_note_id(n, notes_root)
        node_map[nid] = {
            "id": nid,
            "path": nid,
            "title": title_from_file(n),
            "stem": n.stem,
        }
        id_by_stem.setdefault(n.stem.lower(), []).append(nid)

    edges = []
    for n in notes:
        src = rel_note_id(n, notes_root)
        txt = n.read_text(encoding="utf-8", errors="ignore")
        links = [m.group(1).strip() for m in WIKILINK_RE.finditer(txt)]
        for raw in links:
            candidates = id_by_stem.get(Path(raw).name.lower(), [])
            if candidates:
                for dst in candidates:
                    edges.append({"src": src, "dst": dst, "type": "WIKILINK"})
            else:
                ghost = f"ghost/{raw}"
                if ghost not in node_map:
                    node_map[ghost] = {"id": ghost, "path": None, "title": raw, "stem": raw}
                edges.append({"src": src, "dst": ghost, "type": "UNRESOLVED_LINK"})

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "notes_root": str(notes_root),
        "nodes": list(node_map.values()),
        "edges": edges,
        "stats": {
            "notes": len(notes),
            "nodes": len(node_map),
            "edges": len(edges),
        },
    }

    out_path = ROOT / ".neural" / "graph.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"INDEX_OK notes={len(notes)} nodes={len(node_map)} edges={len(edges)} root={notes_root} -> {out_path}")


if __name__ == "__main__":
    main()
