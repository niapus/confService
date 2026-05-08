from abc import ABC, abstractmethod
from contextlib import AbstractContextManager


class MailerInterface(ABC):
    """Интерфейс для отправки email. Позволяет подменять реализацию в тестах."""

    @abstractmethod
    def send(self, subject: str, recipients: list[str], html_body: str, sender: str) -> None:
        """Отправляет одно письмо синхронно."""

    @abstractmethod
    def connect(self) -> AbstractContextManager:
        """Возвращает контекстный менеджер SMTP-соединения для пакетной отправки."""
