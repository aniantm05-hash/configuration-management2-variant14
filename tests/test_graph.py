"""Проверки DFS, циклов, границ и повторного раскрытия вершины."""

import unittest
from pathlib import Path

from depviz.graph import adjacency_text, build_graph
from depviz.testrepo import TestRepository, validate_graph

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def sample(name, depth=10, root="A"):
    """Построить один из проверяемых учебных графов."""
    return build_graph(TestRepository(EXAMPLES / name), root, depth)


class GraphTests(unittest.TestCase):
    """Работать с разными формами графа, а не только с деревом."""

    def test_chain_and_depth(self):
        """Не запрашивать зависимости за заданной границей."""
        graph = sample("chain.json", 1)
        self.assertEqual(graph.edges, {"A": ["B"], "B": []})
        self.assertEqual(graph.truncated, {"B"})
        graph = sample("chain.json", 0)
        self.assertEqual(graph.edges, {"A": []})
        self.assertEqual(graph.truncated, {"A"})

    def test_diamond(self):
        """Общая зависимость остаётся одной вершиной."""
        graph = sample("graph.json")
        self.assertEqual(graph.edges["B"], ["D"])
        self.assertEqual(graph.edges["C"], ["D"])
        self.assertEqual(set(graph.edges), {"A", "B", "C", "D"})
        self.assertFalse(graph.cycles)

    def test_cycle(self):
        """Цикл не вызывает бесконечную рекурсию."""
        graph = sample("cycle.json")
        self.assertEqual(graph.cycles, [("A", "B", "C", "A")])
        self.assertEqual(graph.edges["C"], ["A"])

    def test_shorter_path(self):
        """Поздний короткий путь раскрывает ранее обрезанную вершину."""
        graph = sample("shorter_path.json", 3)
        self.assertEqual(graph.edges["E"], ["F"])
        self.assertNotIn("E", graph.truncated)
        self.assertIn("F", graph.truncated)

    def test_isolated_and_unknown_root(self):
        """Не включать недостижимые узлы и не терять ошибку корня."""
        self.assertEqual(sample("isolated.json").edges, {"A": []})
        with self.assertRaises(ValueError):
            sample("isolated.json", root="Z")

    def test_graph_labels_include_all_versions(self):
        """Версии видны в корне, общих зависимостях и листьях."""
        graph = sample("graph.json")
        self.assertEqual(
            graph.versions,
            {"A": "1.0.0", "B": "2.0.0", "D": "4.0.0", "C": "3.0.0"},
        )
        text = adjacency_text(graph)
        self.assertIn("A@1.0.0 -> B@2.0.0, C@3.0.0", text)
        self.assertIn("D@4.0.0 ->", text)

    def test_boundary_and_cycle_have_versions(self):
        """Граница глубины не лишает узел версии; цикл тоже подписан."""
        graph = sample("chain.json", 1)
        self.assertEqual(graph.versions, {"A": "1.0.0", "B": "2.0.0"})
        self.assertIn("B@2.0.0 -> [граница", adjacency_text(graph))
        self.assertIn(
            "Цикл: A@1.0.0 -> B@2.0.0 -> C@3.0.0 -> A@1.0.0",
            adjacency_text(sample("cycle.json")),
        )

    def test_invalid_test_graph(self):
        """Отвергать повреждённые записи, версии и неизвестные ссылки."""
        valid = {"version": "1.0", "dependencies": []}
        cases = [
            None,
            {},
            {"a": valid},
            {"A": []},
            {"A": {"version": "", "dependencies": []}},
            {"A": {"version": 1, "dependencies": []}},
            {"A": {"version": "1.0\n2", "dependencies": []}},
            {"A": {"version": "1.0", "dependencies": "B"}},
            {"A": {"version": "1.0", "dependencies": ["Z"]}},
            {"A": {"version": "1.0", "dependencies": ["A", "A"]}},
            {"A": {"version": "1.0", "dependencies": [None]}},
            {"A": {"dependencies": []}},
        ]
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    validate_graph(case)
