from typing import List, Optional

from app.infrastructure.interface.mailer import MailerInterface


class EmailService:
    def __init__(self, mailer: MailerInterface, default_sender: str):
        self.__mailer = mailer
        self.__sender = default_sender

    def connect(self):
        return self.__mailer.connect()

    def send_sync(self, subject: str, recipients: List[str], html_body: str, sender: Optional[str] = None):
        """Синхронная отправка (уже в контексте)"""
        self.__mailer.send(
            subject=subject,
            recipients=recipients,
            html_body=html_body,
            sender=sender or self.__sender
        )