"""Безопасное вычисление стандартных environment markers через AST."""

import ast
import operator
import os
import platform
import sys

from depviz.versions import single_match

SINGLE_COMPARISON = 1

VERSION_FIELDS = {
    "python_version",
    "python_full_version",
    "implementation_version",
}
COMPARISONS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}
SYMBOLS = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
}


def environment():
    """Вернуть окружение текущего интерпретатора, без запрошенных extras."""
    version = platform.python_version()
    return {
        "python_version": ".".join(version.split(".")[:2]),
        "python_full_version": version,
        "os_name": os.name,
        "sys_platform": sys.platform,
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "platform_version": platform.version(),
        "platform_machine": platform.machine(),
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": sys.implementation.name,
        "implementation_version": version,
        "extra": "",
    }


def operand(node, values):
    """Разрешить только строковые литералы и известные имена."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in values:
        return values[node.id]
    raise ValueError("недопустимая переменная или литерал marker")


def compare(node, values):
    """Вычислить одно сравнение marker, не исполняя Python-код."""
    if len(node.ops) != SINGLE_COMPARISON:
        raise ValueError("цепочки сравнений в marker не поддерживаются")
    left, right = node.left, node.comparators[0]
    first, second = operand(left, values), operand(right, values)
    operation = type(node.ops[0])
    if operation not in COMPARISONS:
        raise ValueError("неподдерживаемый оператор marker")
    version = any(
        isinstance(item, ast.Name) and item.id in VERSION_FIELDS
        for item in (left, right)
    )
    if version and operation in SYMBOLS:
        return single_match(first, SYMBOLS[operation], second)
    return COMPARISONS[operation](first, second)


def evaluate(node, values):
    """Рекурсивно разобрать and/or и сравнения; вызовы запрещены."""
    if isinstance(node, ast.Compare):
        return compare(node, values)
    if isinstance(node, ast.BoolOp):
        results = [evaluate(child, values) for child in node.values]
        if isinstance(node.op, ast.And):
            return all(results)
        if isinstance(node.op, ast.Or):
            return any(results)
    raise ValueError("неподдерживаемое выражение marker")


def marker_active(marker, values=None):
    """Проверить marker, не скрывая неизвестный синтаксис."""
    if not marker:
        return True
    try:
        tree = ast.parse(marker, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"неподдерживаемый marker: {marker}") from error
    return evaluate(tree.body, environment() if values is None else values)
