import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

from hexcolors.color import HexColor
from hexcolors.errors import SourceError
from hexcolors.finder import (SearchResult, download, save_result, search_file,
                              search_text, search_url)


class TestSearchResult(unittest.TestCase):

    def setUp(self):
        # setUp выполняется перед каждым тестом класса
        self.result = search_text("#fff #000 #FFFFFF #f00 #fff")

    def test_found_in_order(self):
        self.assertEqual(self.result.found, ["#fff", "#000", "#FFFFFF", "#f00", "#fff"])

    def test_unique_merges_short_and_full(self):
        self.assertEqual([c.hex for c in self.result.unique()], ["#ffffff", "#000000", "#ff0000"])

    def test_most_common(self):
        top = self.result.most_common(1)
        self.assertEqual(top, [(HexColor(255, 255, 255), 3)])

    def test_to_text(self):
        text = self.result.to_text()
        self.assertIn("Всего найдено: 5, разных цветов: 3", text)
        self.assertIn("#ffffff = rgb(255, 255, 255)  - встречается 3 раз(а)", text)

    def test_empty(self):
        empty = SearchResult("пусто")
        self.assertEqual(empty.unique(), [])
        self.assertIn("Всего найдено: 0", empty.to_text())


class TestFiles(unittest.TestCase):

    def setUp(self):
        # временная папка удаляется сама после теста
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_search_utf8_file(self):
        path = self.dir / "style.css"
        path.write_text("h1 { color: #c0ffee; } /* комментарий */ p { color: #abc }", encoding="utf-8")
        result = search_file(path)
        self.assertEqual(result.found, ["#c0ffee", "#abc"])
        self.assertEqual(result.source, str(path))

    def test_search_cp1251_file(self):
        path = self.dir / "old.txt"
        path.write_text("Цвет шапки #1a2b3c", encoding="cp1251")
        self.assertEqual(search_file(path).found, ["#1a2b3c"])

    def test_missing_file(self):
        with self.assertRaises(SourceError) as context:
            search_file(self.dir / "нет_такого.txt")
        self.assertIn("не найден", str(context.exception))

    def test_folder_instead_of_file(self):
        with self.assertRaises(SourceError):
            search_file(self.dir)

    def test_save_result(self):
        path = save_result(search_text("#fff"), self.dir / "out.txt")
        self.assertIn("#ffffff", path.read_text(encoding="utf-8"))

    def test_save_to_bad_place(self):
        with self.assertRaises(SourceError):
            save_result(search_text("#fff"), self.dir / "нет_папки" / "out.txt")


class TestUrl(unittest.TestCase):
    """Интернет в тестах не нужен: requests.get подменяем заглушкой (mock)."""

    @patch("hexcolors.finder.requests.get")
    def test_search_url(self, fake_get):
        fake_get.return_value = Mock(text='<div style="color:#ABCDEF">', status_code=200)
        result = search_url("https://example.com")
        self.assertEqual(result.found, ["#ABCDEF"])
        fake_get.assert_called_once()
        self.assertEqual(fake_get.call_args.args[0], "https://example.com")

    @patch("hexcolors.finder.requests.get")
    def test_adds_https(self, fake_get):
        fake_get.return_value = Mock(text="")
        download("example.com")
        self.assertEqual(fake_get.call_args.args[0], "https://example.com")

    @patch("hexcolors.finder.requests.get")
    def test_http_error(self, fake_get):
        response = Mock(status_code=404)
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=response)
        fake_get.return_value = response
        with self.assertRaises(SourceError) as context:
            download("https://example.com/nope")
        self.assertIn("404", str(context.exception))

    @patch("hexcolors.finder.requests.get", side_effect=requests.exceptions.Timeout)
    def test_timeout(self, fake_get):
        with self.assertRaises(SourceError) as context:
            download("https://example.com")
        self.assertIn("не ответил", str(context.exception))

    @patch("hexcolors.finder.requests.get", side_effect=requests.exceptions.ConnectionError("нет сети"))
    def test_no_connection(self, fake_get):
        with self.assertRaises(SourceError) as context:
            download("https://example.com")
        self.assertIn("нет интернета", str(context.exception))

    @patch("hexcolors.finder.requests.get", side_effect=requests.exceptions.InvalidURL("плохая ссылка"))
    def test_bad_url(self, fake_get):
        with self.assertRaises(SourceError) as context:
            download("https://")
        self.assertIn("плохая ссылка", str(context.exception))


if __name__ == "__main__":
    unittest.main()
