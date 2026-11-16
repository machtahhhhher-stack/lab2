import unittest

from hexcolors.finder import check_many, find_colors, first_color, highlight, is_hex_color


class TestValidation(unittest.TestCase):
    """Проверка одной строки целиком."""

    def test_valid_colors(self):
        valid = ["#fff", "#FFF", "#f0a", "#f0a8", "#ff00aa", "#FF00AA",
                 "#Ff00aA", "#000000", "#ff00aa80", "#12345678"]
        for text in valid:
            # subTest - чтобы при ошибке было видно, на каком значении упало
            with self.subTest(text=text):
                self.assertTrue(is_hex_color(text))

    def test_wrong_length(self):
        for text in ["#", "#f", "#ff", "#fffff", "#fffffff", "#ff00aa801"]:
            with self.subTest(text=text):
                self.assertFalse(is_hex_color(text))

    def test_wrong_symbols(self):
        for text in ["#ggg", "#ff00zz", "#12 345", "#fff!", "#-ff", "#ffф"]:
            with self.subTest(text=text):
                self.assertFalse(is_hex_color(text))

    def test_hash_is_required(self):
        for text in ["fff", "ff00aa", "##fff", "# fff", "0xff00aa"]:
            with self.subTest(text=text):
                self.assertFalse(is_hex_color(text))

    def test_spaces_around_are_ignored(self):
        self.assertTrue(is_hex_color("  #abc  "))
        self.assertTrue(is_hex_color("#abc\n"))

    def test_empty_string(self):
        self.assertFalse(is_hex_color(""))
        self.assertFalse(is_hex_color("   "))

    def test_check_many(self):
        result = check_many("#fff, #ggg; #ff00aa  red")
        self.assertEqual(result, {"#fff": True, "#ggg": False, "#ff00aa": True, "red": False})

    def test_check_many_empty(self):
        self.assertEqual(check_many("  "), {})


class TestSearch(unittest.TestCase):
    """Поиск цветов внутри текста."""

    def test_css(self):
        css = "body { color: #333; background: #FAFAFA; border: 1px solid #ff00aa80; }"
        self.assertEqual(find_colors(css), ["#333", "#FAFAFA", "#ff00aa80"])

    def test_html_attribute(self):
        html = '<font color="#ff0000">текст</font><td bgcolor=#00ff00>'
        self.assertEqual(find_colors(html), ["#ff0000", "#00ff00"])

    def test_long_color_is_not_cut(self):
        # без правильного порядка альтернатив нашлось бы "#ff0"
        self.assertEqual(find_colors("#ff00aa"), ["#ff00aa"])

    def test_html_entity_is_not_color(self):
        self.assertEqual(find_colors("&#123; &#xabc; ©"), [])

    def test_hash_inside_word_is_not_color(self):
        self.assertEqual(find_colors("язык C#abc, ссылка page#fff, ##abc"), [])

    def test_letters_after_color(self):
        self.assertEqual(find_colors("#abcz #12345 #1234567 #fffg"), [])

    def test_punctuation_around(self):
        text = "(#abc), [#def]; '#123', \"#456\"."
        self.assertEqual(find_colors(text), ["#abc", "#def", "#123", "#456"])

    def test_start_and_end_of_text(self):
        self.assertEqual(find_colors("#abc"), ["#abc"])
        self.assertEqual(find_colors("цвет #abc"), ["#abc"])

    def test_no_colors(self):
        self.assertEqual(find_colors("в этом тексте нет цветов #, # abc"), [])

    def test_repeats_are_kept(self):
        self.assertEqual(find_colors("#fff #fff #FFF"), ["#fff", "#fff", "#FFF"])

    def test_first_color(self):
        self.assertEqual(first_color("фон #123456, текст #fff"), "#123456")
        self.assertIsNone(first_color("цветов нет"))

    def test_highlight(self):
        self.assertEqual(highlight("a #fff b &#123;"), "a [#fff] b &#123;")


if __name__ == "__main__":
    unittest.main()
