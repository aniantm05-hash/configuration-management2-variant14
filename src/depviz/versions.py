"""Сравнение стабильных числовых версий без packaging и pip."""

import operator
import re

MIN_COMPATIBLE_PARTS = 2

OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}
SPECIFIER = re.compile(r"(===|~=|==|!=|>=|<=|>|<)\s*([\w.*+!-]+)")


def validate_version(value):
    """Принять непустую версию без пробелов и управляющих символов."""
    if not isinstance(value, str):
        raise ValueError("версия пакета должна быть непустой строкой")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", value):
        raise ValueError(f"некорректная версия пакета: {value!r}")
    return value


def release(value):
    """Разобрать стабильный релиз; prerelease не выбирать автоматически."""
    if not re.fullmatch(r"\d+(?:\.\d+)*", value):
        raise ValueError(f"неподдерживаемая версия: {value}")
    return tuple(int(part) for part in value.split("."))


def numeric_compare(left, right, operation):
    """Сравнить релизы с дополнением нулями: 1.0 равно 1."""
    first, second = release(left), release(right)
    width = max(len(first), len(second))
    first += (0,) * (width - len(first))
    second += (0,) * (width - len(second))
    return OPERATORS[operation](first, second)


def single_match(version, operation, target):
    """Поддержать обычные ограничения, wildcard и совместимый релиз."""
    if operation == "===":
        return version == target
    if target.endswith(".*") and operation in {"==", "!="}:
        prefix = release(target[:-2])
        equal = release(version)[: len(prefix)] == prefix
        return equal if operation == "==" else not equal
    if operation == "~=":
        parts = release(target)
        if len(parts) < MIN_COMPATIBLE_PARTS:
            raise ValueError("~= требует хотя бы major.minor")
        prefix = parts[:-1]
        return (
            numeric_compare(version, target, ">=")
            and release(version)[: len(prefix)] == prefix
        )
    if operation not in OPERATORS:
        raise ValueError(f"неподдерживаемое сравнение: {operation}")
    return numeric_compare(version, target, operation)


def satisfies(version, specifier):
    """Проверить все ограничения, соединённые запятыми."""
    if not specifier.strip():
        return True
    parts = specifier.strip().strip("()").split(",")
    for part in parts:
        match = SPECIFIER.fullmatch(part.strip())
        if not match:
            raise ValueError(f"некорректное ограничение версии: {part}")
        if not single_match(version, *match.groups()):
            return False
    return True
