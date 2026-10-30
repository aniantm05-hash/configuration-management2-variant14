"""Первый этап: параметры в формате ключ-значение."""

from depviz.config import read_options


def main(arguments=None):
    """Проверить CLI и напечатать конфигурацию."""
    options = read_options(arguments)
    for name, value in vars(options).items():
        print(f"{name}={value}")
    return 0
