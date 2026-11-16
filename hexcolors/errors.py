"""Собственные исключения программы."""


class ColorError(Exception):
    """Общий предок всех наших ошибок - меню ловит его одним except."""


class InvalidColorError(ColorError):
    """Строка не является цветом в формате HEX."""

    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__(f"'{text}' - это не цвет в формате HEX "
                         f"(нужно #RGB, #RGBA, #RRGGBB или #RRGGBBAA)")


class SourceError(ColorError):
    """Не удалось получить текст из файла или по ссылке."""
