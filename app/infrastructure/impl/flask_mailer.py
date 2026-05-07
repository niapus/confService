from typing import List

from flask_mail import Mail, Message

from app.infrastructure.interface.mailer import MailerInterface


class FlaskMailer(MailerInterface):
    def __init__(self, mail: Mail):
        self.__mail = mail

    def send(self, subject: str, recipients: List[str], html_body: str, sender: str) -> None:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            sender=sender
        )

        self.__mail.send(msg)

    def connect(self):
        return self.__mail.connect()