"""Собственный клиент метаданных пакетов PyPI JSON API."""

from urllib.parse import quote

from depviz.network import fetch_json
from depviz.requirements import normalize, parse_dependencies
from depviz.versions import validate_version


class PyPIRepository:
    """Кешировать метаданные; не устанавливать пакеты."""

    def __init__(self, url, fetch=fetch_json):
        """Сохранить базовый URL и функцию HTTP-запроса."""
        self.url = url.rstrip("/")
        self.fetch = fetch
        self.metadata = {}
        self.versions = {}

    def info(self, name):
        """Загрузить метаданные пакета не более одного раза за запуск."""
        key = normalize(name)
        if key not in self.metadata:
            address = f"{self.url}/{quote(key, safe='')}/json"
            self.metadata[key] = self._info(self.fetch(address))
            self.versions[key] = self.metadata[key]["version"]
        return self.metadata[key]

    def version(self, name):
        """Прочитать настоящую версию из info.version."""
        return self.info(name)["version"]

    def dependencies(self, name):
        """Разобрать активные runtime-зависимости из Requires-Dist."""
        return parse_dependencies(self.info(name))

    @staticmethod
    def _info(document):
        """Проверить структуру JSON и оставить необходимые поля."""
        if not isinstance(document, dict):
            raise ValueError("JSON API должен вернуть объект")
        info = document.get("info")
        if not isinstance(info, dict):
            raise ValueError("в ответе API отсутствует info")
        validate_version(info.get("version"))
        fields = (
            "name",
            "version",
            "requires_dist",
            "requires_python",
            "dynamic",
        )
        return {key: info[key] for key in fields if key in info}
