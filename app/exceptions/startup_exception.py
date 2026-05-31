import sys
from typing import Optional


class StartupException(Exception):
    """Базовое исключение для ошибок инициализации"""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code

    def exit(self) -> None:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {self.message}")
        sys.exit(self.exit_code)


class DatabaseSetupException(StartupException):
    """Ошибка инициализации базы данных (exit code 2)."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Ошибка настройки базы данных: {message}", exit_code=2)


class AdminConfigException(StartupException):
    """Ошибка в конфигурации администраторов"""

    def __init__(self, message: str):
        full_msg = f"Ошибка конфигурации ADMIN_DATA: {message}"
        super().__init__(full_msg, exit_code=3)


class LoggingSetupException(StartupException):
    """Ошибка настройки системы логирования (exit code 1)."""

    def __init__(self, message: str, logs_path: Optional[str] = None) -> None:
        full_msg = f"Ошибка настройки логирования: {message}"
        if logs_path:
            full_msg += f" (путь: {logs_path})"
        super().__init__(full_msg, exit_code=1)


class ConfigValidationException(StartupException):
    """Ошибка валидации конфигурации (обязательные переменные)"""

    def __init__(self, missing_vars: list):
        full_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
        super().__init__(full_msg, exit_code=4)

class EnvironmentValidationException(StartupException):
    """Одна или несколько переменных окружения не прошли валидацию (exit code 4)."""

    def __init__(self, errors: list[str]) -> None:
        full_msg = "Ошибки конфигурации:\n  - " + "\n  - ".join(errors)
        super().__init__(full_msg, exit_code=4)