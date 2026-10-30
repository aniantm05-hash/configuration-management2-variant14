"""HTTP JSON-клиент на стандартной библиотеке."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TIMEOUT_SECONDS = 20
MAX_RESPONSE_BYTES = 12 * 1024 * 1024


def fetch_json(url):
    """Скачать ограниченный JSON-ответ и объяснить сетевые ошибки."""
    headers = {"Accept": "application/json", "User-Agent": "depviz14/1.0"}
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ValueError("слишком большой ответ репозитория")
        return json.loads(raw)
    except HTTPError as error:
        raise ValueError(
            f"репозиторий вернул HTTP {error.code}: {url}"
        ) from error
    except (URLError, TimeoutError, OSError) as error:
        raise ValueError(f"сеть недоступна: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(
            "ответ репозитория не является корректным JSON"
        ) from error
