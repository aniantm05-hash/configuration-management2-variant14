"""Локальный граф с явно заданными версиями тестовых пакетов."""

import json
import re
from pathlib import Path

from depviz.requirements import Requirement
from depviz.versions import validate_version


def validate_package(name):
    """Разрешить только имена из заглавных латинских букв."""
    if not isinstance(name, str):
        raise ValueError("имя тестового пакета должно быть строкой")
    if not re.fullmatch(r"[A-Z]+", name):
        raise ValueError("имена тестовых пакетов: большие латинские буквы")


def validate_children(name, children, names):
    """Проверить тип списка, повторения и существование зависимостей."""
    if not isinstance(children, list):
        raise ValueError(f"зависимости {name} должны быть массивом")
    for child in children:
        validate_package(child)
        if child not in names:
            raise ValueError(f"неизвестная зависимость {name}: {child}")
    if len(set(children)) != len(children):
        raise ValueError(f"повторная зависимость у {name}")


def validate_record(name, record, names):
    """Каждая запись обязана задавать version и dependencies."""
    if not isinstance(record, dict):
        raise ValueError(f"{name}: нужны поля version и dependencies")
    if set(record) != {"version", "dependencies"}:
        raise ValueError(f"{name}: нужны только version и dependencies")
    validate_version(record["version"])
    validate_children(name, record["dependencies"], names)


def validate_graph(document):
    """Проверить граф до начала обхода, включая отдельные вершины."""
    if not isinstance(document, dict):
        raise ValueError("тестовый граф должен быть JSON-объектом")
    if not document:
        raise ValueError("тестовый граф не должен быть пустым")
    for name in document:
        validate_package(name)
    for name, record in document.items():
        validate_record(name, record, document)
    return document


def read_graph(path):
    """Прочитать UTF-8 JSON и объяснить ошибку формата или доступа."""
    try:
        text = Path(path).read_text(encoding="utf-8")
        return validate_graph(json.loads(text))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"не удалось прочитать тестовый граф: {error}"
        ) from error


class TestRepository:
    """Выдать зависимости и версии, записанные в тестовом файле."""

    def __init__(self, path):
        """Сохранить проверенные записи без вымышленных значений."""
        self.records = read_graph(path)
        self.versions = {}

    def record(self, name):
        """Объяснить отсутствие пакета в тестовом репозитории."""
        if name not in self.records:
            raise ValueError(f"пакета {name} нет в тестовом репозитории")
        return self.records[name]

    def version(self, name):
        """Получить явную версию пакета, в том числе на границе глубины."""
        version = self.record(name)["version"]
        self.versions[name] = version
        return version

    def dependencies(self, name):
        """Вернуть прямые зависимости заданной записи."""
        names = self.record(name)["dependencies"]
        return [Requirement(child, "", child) for child in sorted(names)]
