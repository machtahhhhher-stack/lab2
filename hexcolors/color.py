from dataclasses import dataclass

from hexcolors.errors import InvalidColorError
from hexcolors.patterns import CHANNEL, ONE_DIGIT, VALID_COLOR


@dataclass(frozen=True)
class HexColor:
    """Цвет: каналы красный, зелёный, синий (0-255) и прозрачность.

    frozen=True - объект нельзя изменить после создания,
    зато его можно класть в множества и использовать как ключ словаря.
    """

    red: int
    green: int
    blue: int
    alpha: int | None = None  # None - прозрачность не указана

    @classmethod
    def parse(cls, text: str) -> "HexColor":
        """Разбирает строку вида #f0a / #ff00aa80 в объект HexColor."""
        text = text.strip()
        if not VALID_COLOR.match(text):
            raise InvalidColorError(text)
        digits = expand(text[1:])
        # findall режет "ff00aa80" на пары ["ff", "00", "aa", "80"]
        channels = [int(pair, 16) for pair in CHANNEL.findall(digits)]
        return cls(*channels)

    @property
    def hex(self) -> str:
        """Нормальная запись: всегда полная и маленькими буквами."""
        result = f"#{self.red:02x}{self.green:02x}{self.blue:02x}"
        if self.alpha is not None:
            result += f"{self.alpha:02x}"
        return result

    def rgb(self) -> tuple[int, int, int]:
        return self.red, self.green, self.blue

    def css(self) -> str:
        """Тот же цвет в виде функции CSS: rgb(...) или rgba(...)."""
        if self.alpha is None:
            return f"rgb({self.red}, {self.green}, {self.blue})"
        # в CSS прозрачность пишется дробью от 0 до 1
        return f"rgba({self.red}, {self.green}, {self.blue}, {self.alpha / 255:.2f})"

    def __str__(self) -> str:
        return f"{self.hex} = {self.css()}"


def expand(digits: str) -> str:
    """Короткую запись разворачивает в полную: f0a -> ff00aa, f0a8 -> ff00aa88."""
    digits = digits.lower()
    if len(digits) in (3, 4):
        # sub заменяет каждую цифру на неё же два раза (\1\1)
        return ONE_DIGIT.sub(r"\1\1", digits)
    return digits
