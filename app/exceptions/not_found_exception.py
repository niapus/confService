from app.exceptions import AppException


class NotFoundException(AppException):
    """Запрашиваемый ресурс не найден (HTTP 404)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class ConferenceNotFoundException(NotFoundException):
    """Конференция с указанным ID не найдена."""

    def __init__(self, conf_id: int) -> None:
        super().__init__(f"Конференция с id {conf_id} не найдена")


class ApplicationNotFoundException(NotFoundException):
    """Заявка с указанным идентификатором не найдена."""

    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Заявка {identifier} не найдена")


class ThesisNotFoundException(NotFoundException):
    """Файл тезисов с указанным ID не найден."""

    def __init__(self, thesis_id: int) -> None:
        super().__init__(f"Файл тезисов с id {thesis_id} не найден")


class ConferenceFileNotFoundException(NotFoundException):
    """Файл конференции с указанным ID не найден в базе данных."""

    def __init__(self, file_id: int) -> None:
        super().__init__(f"Файл конференции с id {file_id} не найден")


class FileNotFoundException(NotFoundException):
    """Файл с указанным именем не найден на диске."""

    def __init__(self, file_name: str) -> None:
        super().__init__(f"Файл {file_name} не найден")