#!/usr/bin/env python3
"""Optional local BGE-M3 retrieval over an ExoMind graph. No reader/API calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata


def tokens(text):
    folded = ''.join('d' if c in ('đ', 'Đ') else c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c))
    return re.findall(r"[a-z0-9_-]+", folded.lower())


def fingerprint(graph, texts):
    return hashlib.sha256(json.dumps([graph, texts], sort_keys=True).encode()).hexdigest()


def fuse(lexical, dense, topk):
    scores = {}
    for ranking in (lexical, dense):
        for rank, name in enumerate(dict.fromkeys(ranking), 1):
            scores[name] = scores.get(name, 0.0) + 1 / (60 + rank)
    return sorted(scores, key=lambda name: (-scores[name], name))[:topk]


class Hybrid:
    def __init__(self, graph_path, cache_path, model_name, exom, offline=False):
        # Environment set before importing encoder dependencies; note text is never sent to a service.
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        if offline:
            os.environ['HF_HUB_OFFLINE'] = '1'
        import numpy as np
        from sentence_transformers import SentenceTransformer
        self.np = np
        self.graph_path = graph_path.resolve()
        self.cache_path = cache_path
        self.exom = exom
        graph = json.loads(graph_path.read_text())
        root = Path(graph['notes_root']).resolve()
        self.candidate_count = len(graph['nodes'])
        self.nodes = {}
        self.texts = {}
        for node in graph['nodes']:
            if not node.get('path'):
                continue
            source = (root / node['path']).resolve()
            if not source.is_relative_to(root):
                raise ValueError('graph source escapes notes root')
            self.nodes[node['path']] = node
            self.texts[node['path']] = source.read_text()
        if cache_path.resolve() == self.graph_path or cache_path.resolve() in {
                (root / name).resolve() for name in self.nodes}:
            raise ValueError('dense cache must not overwrite graph or source notes')
        self.names = sorted(self.nodes)
        if not self.names:
            raise ValueError('graph has no source notes')
        self.digest = fingerprint(graph, self.texts)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device='cpu', local_files_only=offline)
        self.embeddings = None

    def index(self):
        self.embeddings = self.model.encode([self.texts[n] for n in self.names],
                                           normalize_embeddings=True, batch_size=8,
                                           show_progress_bar=False)
        payload = dict(version=1, fingerprint=self.digest, model=self.model_name,
                       paths=self.names, embeddings=self.embeddings.tolist())
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Private atomic cache: an interrupted write never replaces a valid index.
        with tempfile.NamedTemporaryFile(mode='w', dir=self.cache_path.parent, delete=False) as f:
            temporary = Path(f.name)
            try:
                json.dump(payload, f)
                f.flush()
                os.fsync(f.fileno())
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            temporary.replace(self.cache_path)
        finally:
            temporary.unlink(missing_ok=True)

    def load(self):
        data = json.loads(self.cache_path.read_text())
        if (data.get('version'), data.get('fingerprint'), data.get('model'), data.get('paths')) != (
                1, self.digest, self.model_name, self.names):
            raise ValueError('stale or incompatible dense cache; run index again')
        embeddings = self.np.asarray(data['embeddings'], dtype=self.np.float32)
        if (embeddings.ndim != 2 or embeddings.shape != (
                len(self.names), self.model.get_sentence_embedding_dimension())
                or not self.np.isfinite(embeddings).all()):
            raise ValueError('invalid embedding matrix')
        norms = self.np.linalg.norm(embeddings, axis=1, keepdims=True)
        if (norms == 0).any():
            raise ValueError('zero embedding vector')
        self.embeddings = embeddings / norms

    def search_many(self, queries, topk=5):
        if topk < 1:
            raise ValueError('topk must be positive')
        if self.embeddings is None:
            self.load()
        if not queries:
            return []
        vectors = self.model.encode(queries, normalize_embeddings=True,
                                    batch_size=8, show_progress_bar=False)
        output = []
        for query, vector in zip(queries, vectors):
            if not query.strip():
                output.append([])
                continue
            native = json.loads(subprocess.run(
                [self.exom, 'recall', '--query', query, '--graph', str(self.graph_path),
                 '--topk', str(self.candidate_count), '--json'],
                capture_output=True, text=True, check=True).stdout)['results']
            lexical = [r['path'] for r in native if r['path'] in self.nodes]
            similarity = self.embeddings @ vector
            dense = [self.names[i] for i in self.np.argsort(-similarity, kind='stable')]
            ranked = fuse(lexical, dense, topk)
            output.append([dict(rank=i + 1, path=name, title=self.nodes[name]['title'])
                           for i, name in enumerate(ranked)])
        return output

    def context(self, query, rows, budget):
        # Exact character budget including paths. Original source lines only, no generated summaries.
        blocks = []
        for row in rows:
            lines = self.texts[row['path']].splitlines()
            terms = set(tokens(query))
            best = max(range(len(lines)), key=lambda i: (len(terms & set(tokens(lines[i]))), -i), default=0)
            excerpt = '\n'.join(lines[best:])[:600]
            blocks.append(f"### {row['title']}\nPath: {row['path']}\n{excerpt}\n")
        return '\n'.join(blocks)[:budget]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['index', 'recall', 'pi-context'])
    p.add_argument('--graph', type=Path, required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--model', default='BAAI/bge-m3')
    p.add_argument('--exom', default='exom')
    p.add_argument('--offline', action='store_true')
    p.add_argument('--query')
    p.add_argument('--topk', type=int, default=5)
    p.add_argument('--max-chars', type=int, default=3000)
    args = p.parse_args()
    if args.topk < 1 or args.max_chars < 1:
        p.error('topk and max-chars must be positive')
    if args.command != 'index' and args.query is None:
        p.error('--query is required')
    engine = Hybrid(args.graph, args.cache, args.model, args.exom, args.offline)
    if args.command == 'index':
        engine.index()
        print(json.dumps(dict(indexed=len(engine.names))))
    else:
        rows = engine.search_many([args.query], args.topk)[0]
        if args.command == 'recall':
            print(json.dumps(dict(query=args.query, results=rows), ensure_ascii=False))
        else:
            print(engine.context(args.query, rows, args.max_chars))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'hybrid retrieval failed: {error}', file=sys.stderr)
        raise SystemExit(1)
