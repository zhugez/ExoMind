"""Dependency-free behavioral checks: python3 -m unittest discover -s scripts -p 'test_*.py'."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from exom_hybrid import Hybrid, fingerprint, fuse, tokens
    from benchmark_hybrid import write_report
except ImportError:
    from scripts.exom_hybrid import Hybrid, fingerprint, fuse, tokens
    from scripts.benchmark_hybrid import write_report


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

    def test_diacritic_normalization_matches_native(self):
        self.assertEqual(tokens('Đổi cấu hình'), tokens('doi cau hinh'))
        self.assertEqual(tokens('Đổi cấu hình'), ['doi', 'cau', 'hinh'])

    def test_context_vietnamese_diacritics_normalization(self):
        engine = Hybrid.__new__(Hybrid)
        engine.texts = {'a': '# Header\nIrrelevant line\nĐổi cấu hình hệ thống\nNext line'}
        text = engine.context('doi cau hinh', [dict(path='a', title='A')], 200)
        self.assertIn('Đổi cấu hình hệ thống', text)
        self.assertNotIn('Irrelevant line', text)

        text_accented = engine.context('Đổi cấu hình', [dict(path='a', title='A')], 200)
        self.assertIn('Đổi cấu hình hệ thống', text_accented)
        self.assertNotIn('Irrelevant line', text_accented)

    def test_write_report_creates_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'nested' / 'sub' / 'report.json'
            self.assertFalse(target.parent.exists())
            write_report(target, {'status': 'ok'})
            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(target.read_text()), {'status': 'ok'})

    def test_package_imports_and_context_without_scripts_in_sys_path(self):
        repo_root = Path(__file__).resolve().parent.parent
        script = (
            'from scripts.exom_hybrid import Hybrid, tokens; '
            'from scripts.benchmark_hybrid import write_report; '
            'engine = Hybrid.__new__(Hybrid); '
            'engine.texts = {"note.md": "Đổi cấu hình hệ thống"}; '
            'res = engine.context("doi cau hinh", [{"path": "note.md", "title": "T"}], 100); '
            'assert "Đổi cấu hình" in res'
        )
        proc = subprocess.run([sys.executable, '-c', script], cwd=repo_root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Import/execution failed: {proc.stderr}")


if __name__ == '__main__':
    unittest.main()
