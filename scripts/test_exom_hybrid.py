"""Dependency-free behavioral checks: python3 -m unittest discover -s scripts -p 'test_*.py'."""
import json
from pathlib import Path
import tempfile
import unittest

from exom_hybrid import Hybrid, fingerprint, fuse


class HybridChecks(unittest.TestCase):
    def test_rrf_duplicates_ties_and_dense_fallback(self):
        self.assertEqual(fuse(['a', 'a', 'b'], ['b', 'a'], 5), ['a', 'b'])
        self.assertEqual(fuse([], ['c', 'b'], 1), ['c'])
        self.assertNotEqual(fingerprint({}, {'a': 'old'}), fingerprint({}, {'a': 'new'}))

    def test_stale_cache_rejected_before_matrix_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = Hybrid.__new__(Hybrid)
            engine.cache_path = Path(tmp) / 'cache.json'
            engine.cache_path.write_text(json.dumps(dict(version=1, fingerprint='old')))
            engine.digest, engine.model_name, engine.names = 'new', 'model', ['a']
            with self.assertRaisesRegex(ValueError, 'stale'):
                engine.load()

    def test_context_is_verbatim_and_bounded(self):
        engine = Hybrid.__new__(Hybrid)
        engine.texts = {'a': '# Header\nIrrelevant\nRust tracing evidence\nNext line'}
        text = engine.context('Rust tracing', [dict(path='a', title='A')], 100)
        self.assertIn('Rust tracing evidence', text)
        self.assertNotIn('Irrelevant', text)
        self.assertLessEqual(len(engine.context('Rust', [dict(path='a', title='A')], 12)), 12)


if __name__ == '__main__':
    unittest.main()
