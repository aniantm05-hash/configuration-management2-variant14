"""Метаданные и markers проверяются без сетевого доступа."""

import unittest

from depviz.markers import environment, marker_active
from depviz.pypi import PyPIRepository
from depviz.requirements import parse_dependencies, parse_requirement
from depviz.versions import satisfies


class MetadataTests(unittest.TestCase):
    """Не путать runtime requirements и необязательные extras."""

    def test_requirements(self):
        """Выделить имя, ограничения и условную зависимость."""
        item = parse_requirement("Some_Package (>=1.2,<3)")
        self.assertEqual(item.name, "some-package")
        self.assertEqual(item.specifier, ">=1.2,<3")
        self.assertIsNone(parse_requirement('x; extra == "test"'))
        self.assertIsNone(parse_requirement('x; python_version < "2"'))
        with self.assertRaises(ValueError):
            parse_requirement("x[feature]>=1")

    def test_null_metadata(self):
        """null dynamic допустим, но динамические зависимости не скрываются."""
        self.assertEqual(
            parse_dependencies({"requires_dist": None, "dynamic": None}), []
        )
        with self.assertRaisesRegex(ValueError, "динамические"):
            parse_dependencies(
                {"requires_dist": None, "dynamic": ["requires_dist"]}
            )

    def test_markers(self):
        """Сравнивать версии численно и не исполнять произвольный код."""
        values = environment()
        values["python_version"] = "3.12"
        self.assertTrue(marker_active('python_version > "3.9"', values))
        self.assertFalse(marker_active('extra == "dev"', values))
        self.assertTrue(
            marker_active(
                '(python_version < "3" or python_version >= "3.12")', values
            )
        )
        with self.assertRaises(ValueError):
            marker_active('__import__("os").system("echo bad")')
        with self.assertRaises(ValueError):
            marker_active('unknown == "x"')

    def test_versions(self):
        """Проверить wildcard, ограничения и числовой порядок."""
        self.assertTrue(satisfies("2.10", ">=2.9,<3"))
        self.assertTrue(satisfies("1.9.2", "==1.*"))
        self.assertTrue(satisfies("1.9.2", "~=1.9"))
        self.assertFalse(satisfies("2.0", "~=1.9"))
        self.assertFalse(satisfies("1.9.2", "!=1.9.*"))

    def test_json_cache_and_url(self):
        """Один пакет скачивается один раз с нужного URL."""
        calls = []

        def fake(url):
            """Подставить метаданные вместо HTTP."""
            calls.append(url)
            return {"info": {"version": "1.0", "requires_dist": ["B>=1"]}}

        repo = PyPIRepository("https://example.test/pypi", fake)
        self.assertEqual(repo.dependencies("Some_Package")[0].name, "b")
        repo.dependencies("some-package")
        self.assertEqual(calls, ["https://example.test/pypi/some-package/json"])
        with self.assertRaises(ValueError):
            PyPIRepository._info({"info": {}})

    def test_invalid_api_versions_are_rejected(self):
        """Не подставлять фиктивную версию, если API вернул мусор."""
        for version in [None, "", "1.0\n2", 12]:
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    PyPIRepository._info({"info": {"version": version}})
