"""Второй этап: метаданные из собственного JSON API клиента."""

import sys

from depviz.config import read_options
from depviz.pypi import PyPIRepository

CONFIG_STAGE = 1


def execute(options):
    """Показать конфигурацию или прямые зависимости."""
    if options.stage == CONFIG_STAGE:
        for name, value in vars(options).items():
            print(f"{name}={value}")
        return
    if options.test_repo:
        raise ValueError("анализ тестового графа относится к этапу 3")
    repository = PyPIRepository(options.repository)
    dependencies = repository.dependencies(options.package)
    for dependency in dependencies:
        print(f"{dependency.name} {dependency.specifier}".rstrip())
    if not dependencies:
        print("Прямых зависимостей нет")


def main(arguments=None):
    """Объяснить ошибки сети или метаданных без traceback."""
    options = read_options(arguments)
    try:
        execute(options)
        return 0
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
