"""Регрессии интерфейса: только три этапа и версии в итоговом выводе."""

import contextlib
import io
import unittest
from pathlib import Path

from depviz.cli import main
from depviz.config import read_options

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/graph.json"


class CliTests(unittest.TestCase):
    """Старая команда запуска теперь строит версионный текстовый граф."""

    def test_default_graph(self):
        """Этап 3 работает без Java, PlantUML и сетевых запросов."""
        buffer = io.StringIO()
        args = ["--package", "A", "--test-repo", "--repository", str(EXAMPLE)]
        with contextlib.redirect_stdout(buffer):
            result = main(args)
        self.assertEqual(result, 0)
        self.assertIn("A@1.0.0 -> B@2.0.0, C@3.0.0", buffer.getvalue())
        self.assertNotIn("@startuml", buffer.getvalue())

    def test_stage_four_and_five_are_unavailable(self):
        """Исключённые этапы не остаются скрытыми режимами."""
        for stage in ["4", "5"]:
            with self.subTest(stage=stage):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        read_options(["--package", "A", "--stage", stage])

    def test_default_stage_three(self):
        """Обычный запуск больше не выбирает визуализацию пятого этапа."""
        self.assertEqual(read_options(["--package", "requests"]).stage, 3)
