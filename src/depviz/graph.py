"""Рекурсивный DFS и текстовый граф с версиями всех вершин."""

from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Ребро направлено от пакета к его зависимости."""

    root: str
    edges: dict = field(default_factory=dict)
    constraints: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)
    truncated: set = field(default_factory=set)
    versions: dict = field(default_factory=dict)


def record_cycle(graph, name, path):
    """Запомнить обнаруженный цикл один раз."""
    cycle = path[path.index(name) :] + (name,)
    if cycle not in graph.cycles:
        graph.cycles.append(cycle)


def build_graph(repository, root, max_depth):
    """Пройти граф DFS с рекурсией и повторным раскрытием коротких путей."""
    graph = DependencyGraph(root)
    expanded_depth = {}

    def visit(name, depth, path):
        """Прочитать версию, затем раскрыть разрешённые глубиной рёбра."""
        graph.edges.setdefault(name, [])
        graph.versions[name] = repository.version(name)
        if name in path:
            record_cycle(graph, name, path)
            return
        if name in expanded_depth and expanded_depth[name] <= depth:
            return
        if depth >= max_depth:
            graph.truncated.add(name)
            return
        expanded_depth[name] = depth
        graph.truncated.discard(name)
        requirements = repository.dependencies(name)
        graph.edges[name] = sorted({item.name for item in requirements})
        for item in requirements:
            graph.constraints[name, item.name] = item.specifier
            visit(item.name, depth + 1, path + (name,))

    visit(root, 0, ())
    return graph


def package_label(graph, name):
    """Одинаково подписать корень, листья и участники цикла."""
    return f"{name}@{graph.versions[name]}"


def adjacency_line(graph, name, children):
    """Отличить подтверждённый лист от границы анализа."""
    if name in graph.truncated:
        tail = "[граница глубины; зависимости не раскрыты]"
    elif children:
        tail = ", ".join(package_label(graph, child) for child in children)
    else:
        tail = "—"
    return f"{package_label(graph, name)} -> {tail}"


def adjacency_text(graph):
    """Показать список смежности с точными версиями и циклами."""
    lines = [
        adjacency_line(graph, name, children)
        for name, children in sorted(graph.edges.items())
    ]
    for cycle in graph.cycles:
        labels = [package_label(graph, name) for name in cycle]
        lines.append("Цикл: " + " -> ".join(labels))
    return "\n".join(lines)
