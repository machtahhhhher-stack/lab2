from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import requests

from hexcolors.color import HexColor
from hexcolors.errors import SourceError
from hexcolors.patterns import SEARCH_COLOR, SEPARATORS, VALID_COLOR

# некоторые сайты (та же Википедия) не отвечают запросам без User-Agent
HEADERS = {"User-Agent": "Mozilla/5.0 (lab2 hex color finder)"}
TIMEOUT = 10  # секунд, чтобы программа не зависла на медленном сайте


@dataclass
class SearchResult:
    """Что нашли и где: источник + список цветов в порядке появления."""

    source: str
    found: list[str] = field(default_factory=list)

    @property
    def colors(self) -> list[HexColor]:
        return [HexColor.parse(text) for text in self.found]

    def unique(self) -> list[HexColor]:
        """Без повторов. #FFF и #ffffff считаются одним цветом."""
        return list(dict.fromkeys(self.colors))

    def most_common(self, count: int = 10) -> list[tuple[HexColor, int]]:
        return Counter(self.colors).most_common(count)

    def to_text(self) -> str:
        """Отчёт для сохранения в файл."""
        lines = [f"Источник: {self.source}",
                 f"Всего найдено: {len(self.found)}, разных цветов: {len(self.unique())}",
                 ""]
        for color, times in self.most_common(count=len(self.found)):
            lines.append(f"{color}  - встречается {times} раз(а)")
        return "\n".join(lines) + "\n"


def is_hex_color(text: str) -> bool:
    """True, если вся строка - это корректный HEX-цвет."""
    return VALID_COLOR.match(text.strip()) is not None


def check_many(text: str) -> dict[str, bool]:
    """Проверяет несколько значений, введённых через пробел, запятую или ;."""
    values = [part for part in SEPARATORS.split(text.strip()) if part]
    return {value: is_hex_color(value) for value in values}


def find_colors(text: str) -> list[str]:
    """Все цвета в тексте в том виде, как они там записаны."""
    # в регулярке одна группа, поэтому findall вернёт только цифры без #
    return ["#" + digits for digits in SEARCH_COLOR.findall(text)]


def first_color(text: str) -> str | None:
    """Первый цвет в тексте или None, если цветов нет."""
    match = SEARCH_COLOR.search(text)
    return match.group(0) if match else None


def highlight(text: str) -> str:
    """Помечает найденные цвета скобками - удобно смотреть глазами."""
    return SEARCH_COLOR.sub(lambda m: f"[{m.group(0)}]", text)


def search_text(text: str, source: str = "введённый текст") -> SearchResult:
    return SearchResult(source, find_colors(text))


def read_file(path: str | Path) -> str:
    path = Path(path)
    try:
        with open(path, encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        raise SourceError(f"Файл не найден: {path}") from None
    except UnicodeDecodeError:
        # файл не в UTF-8 - пробуем старую русскую кодировку Windows
        return path.read_text(encoding="cp1251", errors="replace")
    except OSError as error:
        raise SourceError(f"Не удалось прочитать {path}: {error}") from error


def search_file(path: str | Path) -> SearchResult:
    return SearchResult(str(path), find_colors(read_file(path)))


def download(url: str) -> str:
    """Скачивает страницу по ссылке и возвращает её HTML-код."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()  # 404, 500 и т.п. -> исключение HTTPError
    except requests.exceptions.HTTPError as error:
        raise SourceError(f"Сайт ответил ошибкой {error.response.status_code}: {url}") from error
    except requests.exceptions.Timeout:
        raise SourceError(f"Сайт не ответил за {TIMEOUT} секунд: {url}") from None
    except requests.exceptions.ConnectionError:
        # сайта не существует или нет интернета - подробности пользователю не нужны
        raise SourceError(f"Не удалось подключиться к {url} "
                          f"(нет интернета или неверный адрес)") from None
    except requests.exceptions.RequestException as error:
        # всё остальное: кривая ссылка, слишком много перенаправлений и т.п.
        raise SourceError(f"Не удалось открыть {url}: {error}") from error
    return response.text


def search_url(url: str) -> SearchResult:
    return SearchResult(url, find_colors(download(url)))


def save_result(result: SearchResult, path: str | Path) -> Path:
    path = Path(path)
    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(result.to_text())
    except OSError as error:
        raise SourceError(f"Не удалось записать {path}: {error}") from error
    return path
