import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from hexcolors.errors import SourceError
from hexcolors.finder import SearchResult
from main import App, handle_errors


def run_with_input(func, *answers: str) -> str:
    """Запускает функцию, подставляя ответы вместо ввода с клавиатуры.
    Возвращает всё, что функция напечатала."""
    output = io.StringIO()
    with patch("builtins.input", side_effect=list(answers)), redirect_stdout(output):
        func()
    return output.getvalue()


class TestDecorator(unittest.TestCase):

    def test_catches_our_errors(self):
        @handle_errors
        def broken():
            raise SourceError("что-то сломалось")

        output = io.StringIO()
        with redirect_stdout(output):
            self.assertIsNone(broken())
        self.assertIn("Ошибка: что-то сломалось", output.getvalue())

    def test_passes_result_and_keeps_name(self):
        @handle_errors
        def add(a, b):
            return a + b

        self.assertEqual(add(2, b=3), 5)
        self.assertEqual(add.__name__, "add")  # спасибо functools.wraps

    def test_other_errors_are_not_hidden(self):
        @handle_errors
        def bug():
            raise ZeroDivisionError

        with self.assertRaises(ZeroDivisionError):
            bug()


class TestApp(unittest.TestCase):

    def setUp(self):
        self.app = App()

    def test_check(self):
        out = run_with_input(self.app.check, "#fff, #ggg")
        self.assertIn("#fff", out)
        self.assertIn("корректный", out)
        self.assertIn("НЕ цвет", out)

    def test_check_empty(self):
        self.assertIn("Ничего не введено", run_with_input(self.app.check, ""))

    def test_find_in_text(self):
        out = run_with_input(self.app.find_in_text, "фон #000, текст #fff")
        self.assertIn("Найдено цветов: 2", out)
        self.assertIn("[#000]", out)
        self.assertEqual(self.app.last.found, ["#000", "#fff"])

    def test_find_in_demo_file(self):
        out = run_with_input(self.app.find_in_file, "")
        self.assertIn("style.css", out)
        self.assertIn("#ff4081", out)

    def test_find_in_missing_file(self):
        out = run_with_input(self.app.find_in_file, "нет_такого_файла.css")
        self.assertIn("Ошибка: Файл не найден", out)

    @patch("main.search_url")
    def test_find_on_page(self, fake_search):
        fake_search.return_value = SearchResult("https://x.ru", ["#abc"])
        out = run_with_input(self.app.find_on_page, "https://x.ru")
        fake_search.assert_called_once_with("https://x.ru")
        self.assertIn("Найдено цветов: 1", out)

    @patch("main.search_url")
    def test_find_on_page_default_url(self, fake_search):
        fake_search.return_value = SearchResult("demo", [])
        run_with_input(self.app.find_on_page, "")
        fake_search.assert_called_once_with("https://en.wikipedia.org/wiki/Web_colors")

    def test_save_without_result(self):
        self.assertIn("Сначала", run_with_input(self.app.save))

    def test_save(self):
        self.app.last = SearchResult("тест", ["#fff"])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "res.txt")
            out = run_with_input(self.app.save, path)
            self.assertIn("Сохранено", out)
            self.assertTrue(os.path.exists(path))

    def test_details(self):
        out = run_with_input(self.app.details, "#ff000080")
        self.assertIn("#ff000080", out)
        self.assertIn("(255, 0, 0)", out)
        self.assertIn("128 из 255", out)

    def test_details_invalid(self):
        self.assertIn("Ошибка", run_with_input(self.app.details, "красный"))

    def test_run_menu(self):
        out = run_with_input(self.app.run, "9", "6", "#fff", "0")
        self.assertIn("Нет такого пункта", out)
        self.assertIn("rgb(255, 255, 255)", out)
        self.assertIn("Пока!", out)

    def test_run_ctrl_c(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(io.StringIO()) as out:
            self.app.run()
        self.assertIn("Пока!", out.getvalue())


if __name__ == "__main__":
    unittest.main()
