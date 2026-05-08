from app.exceptions import AppException


class ConflictException(AppException):
    """Конфликт с текущим состоянием ресурса (HTTP 409)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409)


class ApplicationAfterDeadlineException(ConflictException):
    """Дедлайн подачи заявки истёк."""

    def __init__(self, date: str) -> None:
        super().__init__(f"Дедлайн подачи заявки истек {date}")


class ApplicationAlreadyExists(ConflictException):
    """Заявка с таким email уже зарегистрирована."""

    def __init__(self, email: str) -> None:
        super().__init__(f"Заявка с таким email {email} уже существует")


class ThesisAfterDeadlineException(ConflictException):
    """Дедлайн подачи тезисов истёк."""

    def __init__(self, date: str) -> None:
        super().__init__(f"Дедлайн подачи тезисов истек {date}")


class ConferenceAlreadyEndedException(ConflictException):
    """Конференция уже завершилась."""

    def __init__(self, conf_id: int) -> None:
        super().__init__(f"Конференция с id {conf_id} уже прошла")