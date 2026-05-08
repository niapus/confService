from app.exceptions import AppException


class ConversionException(AppException):
    """Ошибка преобразования поля формы (HTTP 400). Несёт имя поля и сообщение."""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}", status_code=400)


class EmptyRequiredFieldException(ConversionException):
    """Обязательное поле не заполнено."""

    def __init__(self, field: str) -> None:
        super().__init__(field, "Поле не может быть пустым")


class InvalidFieldFormatException(ConversionException):
    """Значение поля не соответствует ожидаемому формату."""

    def __init__(self, field: str, details: str | None = None) -> None:
        msg = "Неверный формат" + (f": {details}" if details else "")
        super().__init__(field, msg)