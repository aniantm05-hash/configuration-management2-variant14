"""Аргументы CLI и небольшие независимые проверки конфигурации."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

MAX_DEPTH = 100
MIN_DEPTH = 0
DEFAULT_DEPTH = 3
DEFAULT_REPOSITORY = "https://pypi.org/pypi"
NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"


def package_name(value):
    """Проверить имя пакета."""
    if not re.fullmatch(NAME_PATTERN, value):
        raise argparse.ArgumentTypeError("некорректное имя пакета")
    return value


def depth_value(value):
    """Проверить целую глубину от нуля до установленного предела."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("глубина должна быть целой") from error
    if not MIN_DEPTH <= number <= MAX_DEPTH:
        message = f"глубина должна быть от {MIN_DEPTH} до {MAX_DEPTH}"
        raise argparse.ArgumentTypeError(message)
    return number


def parser():
    """Создать параметры только первых трёх этапов."""
    result = argparse.ArgumentParser(description="Граф зависимостей Python")
    result.add_argument("--package", required=True, type=package_name)
    result.add_argument("--repository", default=DEFAULT_REPOSITORY)
    result.add_argument("--test-repo", action="store_true")
    result.add_argument("--max-depth", type=depth_value, default=DEFAULT_DEPTH)
    result.add_argument("--stage", type=int, choices=range(1, 3), default=2)
    return result


def validate_test_source(options):
    """Тестовый режим требует заглавное имя и существующий файл."""
    if not re.fullmatch(r"[A-Z]+", options.package):
        raise ValueError("тестовый пакет: только большие латинские буквы")
    if not Path(options.repository).is_file():
        raise ValueError(f"тестовый файл не найден: {options.repository}")


def validate_url_shape(address):
    """Проверить схему, сервер и корректность порта URL."""
    if any(char.isspace() for char in address):
        raise ValueError("URL не должен содержать пробелы")
    url = urlsplit(address)
    if url.scheme not in {"http", "https"}:
        raise ValueError("репозиторий: HTTP(S) URL JSON API")
    if not url.hostname:
        raise ValueError("в URL не указан сервер")
    _ = url.port
    return url


def validate_url_details(url):
    """Отклонить credentials и параметры, меняющие путь JSON API."""
    fields = (url.query, url.fragment, url.username, url.password)
    if any(fields):
        raise ValueError("URL не должен содержать пароль, query или fragment")


def validate_source(options):
    """Выбрать проверку файла либо сетевого репозитория."""
    if options.test_repo:
        validate_test_source(options)
        return
    validate_url_details(validate_url_shape(options.repository))


def read_options(arguments=None):
    """Разобрать параметры и вывести ошибки средствами argparse."""
    cli = parser()
    options = cli.parse_args(arguments)
    try:
        validate_source(options)
    except ValueError as error:
        cli.error(str(error))
    return options
