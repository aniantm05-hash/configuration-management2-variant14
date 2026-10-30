"""Проверка цикломатической сложности Radon, включая вложенные функции."""

import json
from pathlib import Path

MAX_COMPLEXITY = 10


def walk_blocks(blocks):
    """Обойти функции, методы и closures, не пропустив вложенный DFS."""
    for block in blocks:
        yield block
        yield from walk_blocks(getattr(block, "methods", []))
        yield from walk_blocks(getattr(block, "closures", []))


def complexity_records(root):
    """Проверить весь Python-код, а не только каталог src."""
    from radon.complexity import cc_visit

    records = []
    for directory in ("src", "tests", "scripts"):
        for path in sorted((root / directory).rglob("*.py")):
            blocks = cc_visit(path.read_text(encoding="utf-8"))
            for block in walk_blocks(blocks):
                records.append(
                    {
                        "file": str(path.relative_to(root)),
                        "line": block.lineno,
                        "name": block.name,
                        "complexity": block.complexity,
                    }
                )
    return records


def main():
    """Сообщить максимум и завершиться ошибкой при превышении 10."""
    root = Path(__file__).resolve().parents[1]
    try:
        records = complexity_records(root)
    except ImportError:
        print("Установите: python3 -m pip install -r requirements-dev.txt")
        return 1
    report = {
        "tool": "Radon 6.0.1",
        "limit": MAX_COMPLEXITY,
        "maximum": max(row["complexity"] for row in records),
        "blocks": records,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(any(row["complexity"] > MAX_COMPLEXITY for row in records))


if __name__ == "__main__":
    raise SystemExit(main())
