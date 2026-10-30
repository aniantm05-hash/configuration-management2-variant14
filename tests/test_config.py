"""Проверки всех параметров CLI."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from depviz.config import read_options


class ConfigurationTests(unittest.TestCase):
    """Ошибки ввода не должны приводить к traceback."""

    def reject(self, args):
        """Перехватить понятную диагностическую ошибку argparse."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                read_options(args)
        self.assertEqual(raised.exception.code, 2)

    def test_valid_defaults(self):
        """Принять настоящее имя и стандартный URL."""
        options = read_options(["--package", "requests"])
        self.assertEqual(options.max_depth, 3)
        self.assertFalse(options.test_repo)

    def test_invalid_parameters(self):
        """Отвергнуть имя, глубину, URL и неизвестный аргумент."""
        cases = [
            [],
            ["--package", "bad name"],
            ["--package", "A", "--max-depth", "-1"],
            ["--package", "A", "--max-depth", "101"],
            ["--package", "A", "--max-depth", "x"],
            ["--package", "A", "--repository", "file:///tmp/a"],
            ["--package", "A", "--unknown"],
            ["--package", "A", "--test-repo", "true"],
        ]
        for args in cases:
            with self.subTest(args=args):
                self.reject(args)

    def test_test_mode(self):
        """Тестовый режим требует доступный файл и заглавное имя."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text("{}", encoding="utf-8")
            args = ["--package", "A", "--test-repo", "--repository"]
            options = read_options(args + [str(path)])
            self.assertTrue(options.test_repo)
            self.reject(
                ["--package", "a", "--test-repo", "--repository", str(path)]
            )
        self.reject(args + [str(path)])
