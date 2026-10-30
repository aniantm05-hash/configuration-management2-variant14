"""Автоматическая проверка измеримых правил из PDF задания."""

import ast
from pathlib import Path

MAX_FILE_LINES = 1000
MAX_LINE_LENGTH = 80
MAX_FUNCTION_LINES = 40
MAX_ARGUMENTS = 7


def function_errors(node, path):
    """Проверить размер, аргументы и наличие docstring у функции."""
    errors = []
    if node.end_lineno - node.lineno + 1 > MAX_FUNCTION_LINES:
        errors.append(f"{path}:{node.lineno}: функция длиннее 40 строк")
    arguments = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    if len(arguments) > MAX_ARGUMENTS:
        errors.append(f"{path}:{node.lineno}: больше 7 аргументов")
    if not ast.get_docstring(node):
        errors.append(f"{path}:{node.lineno}: нет docstring")
    return errors


def inspect_file(path):
    """Проверить Python-файл без сторонних библиотек."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors = []
    if len(lines) > MAX_FILE_LINES:
        errors.append(f"{path}: больше 1000 строк")
    for number, line in enumerate(lines, 1):
        if len(line) > MAX_LINE_LENGTH:
            errors.append(f"{path}:{number}: строка длиннее 80 символов")
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            errors.extend(function_errors(node, path))
    return errors


def main():
    """Завершить проверку ненулевым кодом при нарушениях."""
    root = Path(__file__).resolve().parents[1]
    files = [
        path
        for directory in ("src", "tests", "scripts")
        for path in (root / directory).rglob("*.py")
    ]
    errors = [error for path in files for error in inspect_file(path)]
    for error in errors:
        print(error)
    if not errors:
        print(f"Проверены {len(files)} Python-файла: нарушений нет")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
