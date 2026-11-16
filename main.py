"""Лабораторная работа №2. Вариант 7 - цвета в формате HEX.

Запуск: python main.py
"""
import functools
from pathlib import Path
from typing import Callable

from hexcolors.color import HexColor
from hexcolors.errors import ColorError
from hexcolors.finder import (SearchResult, check_many, highlight, save_result,
                              search_file, search_text, search_url)

DATA_DIR = Path(__file__).parent / "data"
DEMO_URL = "https://en.wikipedia.org/wiki/Web_colors"
TOP = 10  # сколько самых частых цветов показывать

MENU = """
=== Поиск HEX-цветов ===
1. Проверить значения (ввод с клавиатуры)
2. Найти цвета во введённом тексте
3. Найти цвета в файле
4. Найти цвета на веб-странице по ссылке
5. Сохранить последний результат в файл
6. Подробно о цвете
0. Выход"""


def handle_errors(func: Callable) -> Callable:
    """Декоратор: ловит наши ошибки, печатает их, и меню работает дальше."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ColorError as error:
            print(f"Ошибка: {error}")
            return None
    return wrapper


class App:
    """Консольное меню. Помнит последний результат поиска, чтобы его сохранить."""

    def __init__(self) -> None:
        self.last: SearchResult | None = None
        self.actions: dict[str, Callable[[], None]] = {
            "1": self.check,
            "2": self.find_in_text,
            "3": self.find_in_file,
            "4": self.find_on_page,
            "5": self.save,
            "6": self.details,
        }

    def run(self) -> None:
        while True:
            print(MENU)
            try:
                choice = input("> ").strip()
            except (KeyboardInterrupt, EOFError):
                choice = "0"
            if choice == "0":
                print("Пока!")
                return
            action = self.actions.get(choice)
            if action is None:
                print("Нет такого пункта")
            else:
                action()

    @handle_errors
    def check(self) -> None:
        text = input("Введите один или несколько цветов (через пробел или запятую): ")
        results = check_many(text)
        if not results:
            print("Ничего не введено")
        for value, ok in results.items():
            print(f"  {value:<14} {'корректный' if ok else 'НЕ цвет'}")

    @handle_errors
    def find_in_text(self) -> None:
        text = input("Введите текст: ")
        self.show(search_text(text))
        print("Где нашлись:", highlight(text))

    @handle_errors
    def find_in_file(self) -> None:
        print(f"Примеры файлов лежат в папке {DATA_DIR}")
        path = input("Путь к файлу (Enter - data/style.css): ").strip().strip('"')
        self.show(search_file(path or DATA_DIR / "style.css"))

    @handle_errors
    def find_on_page(self) -> None:
        url = input(f"Ссылка (Enter - {DEMO_URL}): ").strip()
        print("Загружаю страницу...")
        self.show(search_url(url or DEMO_URL))

    @handle_errors
    def save(self) -> None:
        if self.last is None:
            print("Сначала что-нибудь найдите (пункты 2-4)")
            return
        name = input("Имя файла (Enter - result.txt): ").strip() or "result.txt"
        print(f"Сохранено: {save_result(self.last, name).resolve()}")

    @handle_errors
    def details(self) -> None:
        color = HexColor.parse(input("Цвет: "))
        print(f"  полная запись: {color.hex}")
        print(f"  RGB:           {color.rgb()}")
        print(f"  CSS:           {color.css()}")
        if color.alpha is not None:
            print(f"  прозрачность:  {color.alpha} из 255")

    def show(self, result: SearchResult) -> None:
        self.last = result
        print(f"\nИсточник: {result.source}")
        print(f"Найдено цветов: {len(result.found)}, разных: {len(result.unique())}")
        if result.found:
            print(f"Самые частые (до {TOP}):")
            for color, times in result.most_common(TOP):
                print(f"  {color}  x{times}")


if __name__ == "__main__":
    App().run()
