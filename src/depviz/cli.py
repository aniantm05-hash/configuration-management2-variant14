"""CLI: конфигурация, прямые зависимости и рекурсивный DFS."""

import sys

from depviz.config import read_options
from depviz.graph import adjacency_text, build_graph
from depviz.pypi import PyPIRepository
from depviz.requirements import normalize
from depviz.testrepo import TestRepository

CONFIG_STAGE = 1
DIRECT_STAGE = 2


def repository_for(options):
    """Выбрать реальный JSON API или локальный тестовый репозиторий."""
    if options.test_repo:
        return TestRepository(options.repository), options.package
    return PyPIRepository(options.repository), normalize(options.package)


def execute(options):
    """Выполнить поведение выбранного учебного этапа."""
    if options.stage == CONFIG_STAGE:
        for name, value in vars(options).items():
            print(f"{name}={value}")
        return
    repository, root = repository_for(options)
    if options.stage == DIRECT_STAGE:
        dependencies = repository.dependencies(root)
        for item in dependencies:
            print(f"{item.name} {item.specifier}".rstrip())
        if not dependencies:
            print("Прямых зависимостей нет")
        return
    graph = build_graph(repository, root, options.max_depth)
    print(adjacency_text(graph))


def main(arguments=None):
    """Завершить CLI ненулевым кодом при диагностируемой ошибке."""
    options = read_options(arguments)
    try:
        execute(options)
        return 0
    except (ValueError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
