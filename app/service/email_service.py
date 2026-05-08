from app.infrastructure.interface.mailer import MailerInterface


class EmailService:
    """Синхронная отправка писем через SMTP-подключение."""

    def __init__(self, mailer: MailerInterface, default_sender: str) -> None:
        self.__mailer = mailer
        self.__sender = default_sender

    def connect(self):
        """Открывает SMTP-соединение. Возвращает контекстный менеджер соединения."""
        return self.__mailer.connect()

    def send_sync(
        self, subject: str, recipients: list[str], html_body: str, sender: str | None = None
    ) -> None:
        """Отправляет письмо синхронно. Использует default_sender если sender не указан."""
        self.__mailer.send(
            subject=subject,
            recipients=recipients,
            html_body=html_body,
            sender=sender or self.__sender
        )
