from contextlib import AbstractContextManager

from flask_mail import Mail, Message

from app.infrastructure.interface.mailer import MailerInterface


class FlaskMailer(MailerInterface):
    """Реализация MailerInterface через Flask-Mail."""

    def __init__(self, mail: Mail) -> None:
        self.__mail = mail

    def send(self, subject: str, recipients: list[str], html_body: str, sender: str) -> None:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            sender=sender
        )
        self.__mail.send(msg)

    def connect(self) -> AbstractContextManager:
        return self.__mail.connect()
