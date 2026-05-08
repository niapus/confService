from app.exceptions import AppException


class FileException(AppException):
    """Ошибка валидации загружаемого файла (HTTP 400)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class FileNullNameException(FileException):
    """Имя файла пустое."""

    def __init__(self) -> None:
        super().__init__("Имя файла пустое")


class FileExtensionException(FileException):
    """Расширение файла не входит в список допустимых."""

    def __init__(self, current: str) -> None:
        super().__init__(f"Недопустимый тип файла {current}")


class FileSizeException(FileException):
    """Размер файла превышает допустимый лимит."""

    def __init__(self, size: int) -> None:
        super().__init__(f"Файл слишком большой. Максимальный размер {size}MB")


class FileSignatureException(FileException):
    """Сигнатура файла не соответствует его расширению."""

    def __init__(self, message: str) -> None:
        super().__init__(message)