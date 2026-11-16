import unittest

from hexcolors.color import HexColor, expand
from hexcolors.errors import ColorError, InvalidColorError


class TestHexColor(unittest.TestCase):

    def test_parse_full(self):
        color = HexColor.parse("#FF00AA")
        self.assertEqual(color.rgb(), (255, 0, 170))
        self.assertIsNone(color.alpha)

    def test_parse_short(self):
        self.assertEqual(HexColor.parse("#f0a"), HexColor(255, 0, 170))

    def test_parse_with_alpha(self):
        self.assertEqual(HexColor.parse("#ff00aa80"), HexColor(255, 0, 170, 128))
        self.assertEqual(HexColor.parse("#f0a8"), HexColor(255, 0, 170, 136))

    def test_short_and_full_are_equal(self):
        self.assertEqual(HexColor.parse("#FFF"), HexColor.parse("#ffffff"))

    def test_hex_is_normalized(self):
        self.assertEqual(HexColor.parse("#F0A").hex, "#ff00aa")
        self.assertEqual(HexColor.parse("#F0A8").hex, "#ff00aa88")

    def test_css(self):
        self.assertEqual(HexColor.parse("#000").css(), "rgb(0, 0, 0)")
        self.assertEqual(HexColor.parse("#ffffff80").css(), "rgba(255, 255, 255, 0.50)")

    def test_str(self):
        self.assertEqual(str(HexColor.parse("#f00")), "#ff0000 = rgb(255, 0, 0)")

    def test_invalid_raises(self):
        for text in ["fff", "#ggg", "#ff", ""]:
            with self.subTest(text=text):
                with self.assertRaises(InvalidColorError):
                    HexColor.parse(text)

    def test_error_is_color_error(self):
        # наше исключение должно ловиться общим предком
        with self.assertRaises(ColorError) as context:
            HexColor.parse("#xyz")
        self.assertIn("#xyz", str(context.exception))
        self.assertEqual(context.exception.text, "#xyz")

    def test_frozen(self):
        color = HexColor(1, 2, 3)
        with self.assertRaises(AttributeError):
            color.red = 10

    def test_can_be_used_in_set(self):
        colors = {HexColor.parse("#fff"), HexColor.parse("#FFFFFF"), HexColor.parse("#000")}
        self.assertEqual(len(colors), 2)


class TestExpand(unittest.TestCase):

    def test_short(self):
        self.assertEqual(expand("f0a"), "ff00aa")
        self.assertEqual(expand("F0A8"), "ff00aa88")

    def test_full_is_unchanged(self):
        self.assertEqual(expand("ff00aa"), "ff00aa")
        self.assertEqual(expand("FF00AA80"), "ff00aa80")


if __name__ == "__main__":
    unittest.main()
