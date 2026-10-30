"""Разбор Requires-Dist из JSON API репозитория Python."""

import re
from dataclasses import dataclass

from depviz.config import NAME_PATTERN
from depviz.markers import marker_active


@dataclass(frozen=True)
class Requirement:
    """Имя зависимости, ограничение версии и исходная строка."""

    name: str
    specifier: str
    text: str


def normalize(name):
    """Нормализация имён дистрибутивов по правилам Python index."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement(text):
    """Отфильтровать необязательные зависимости и разобрать активные."""
    if not isinstance(text, str):
        raise ValueError("Requires-Dist должен содержать строки")
    declaration, _, marker = text.partition(";")
    if not marker_active(marker.strip()):
        return None
    match = re.fullmatch(rf"({NAME_PATTERN})(.*)", declaration.strip())
    if not match:
        raise ValueError(f"неверный Requires-Dist: {text}")
    name, specifier = match.groups()
    specifier = specifier.strip().strip("()").strip()
    if specifier.startswith(("[", "@")):
        raise ValueError(f"extras и прямые URL не поддерживаются: {text}")
    return Requirement(normalize(name), specifier, text)


def parse_dependencies(info):
    """Получить активные runtime-зависимости текущего окружения."""
    raw = info.get("requires_dist")
    if raw is None:
        if "requires_dist" in (info.get("dynamic") or []):
            raise ValueError("динамические зависимости требуют wheel metadata")
        return []
    if not isinstance(raw, list):
        raise ValueError("requires_dist должен быть массивом или null")
    parsed = [parse_requirement(item) for item in raw]
    return sorted((item for item in parsed if item), key=lambda r: r.name)
