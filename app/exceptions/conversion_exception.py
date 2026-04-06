from app.exceptions import AppException


class ConversionException(AppException):
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}", status_code=400)

class EmptyRequiredFieldException(ConversionException):
    def __init__(self, field: str):
        super().__init__(field, "Поле не может быть пустым")

class InvalidFieldFormatException(ConversionException):
    def __init__(self, field: str, details: str = None):
        msg = "Неверный формат" + (f": {details}" if details else "")
        super().__init__(field, msg)