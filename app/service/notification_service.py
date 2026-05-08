from typing import Any

from flask import url_for, render_template
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.conference import Conference
from app.models.email_queue import QueueType
from app.models.thesis import Thesis
from app.service.email_queue_service import EmailQueueService


class NotificationService:
    """Отправка email-уведомлений участникам через очередь писем."""

    def __init__(
        self, email_queue: EmailQueueService, mail_enabled: bool, verification_enabled: bool
    ) -> None:
        self.__email_queue = email_queue
        self.mail_enabled = mail_enabled
        self.verification_enabled = verification_enabled

    def send_verification_email(
        self, token: str, application: Application, conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь письмо с ссылкой для подтверждения email."""
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        html = render_template(
            'email/verification.html',
            application=application,
            conference=conference,
            verification_url=verification_url
        )
        self._send_email(
            subject=f"Подтверждение - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    def send_registration_confirmed(self, application: Application, session: Session) -> None:
        """Ставит в очередь письмо об успешном подтверждении регистрации."""
        conference = application.conference
        html = render_template(
            'email/registration_confirmed.html',
            application=application,
            conference=conference,
            conference_url=self._get_conference_url(conference)
        )
        self._send_email(
            subject=f"Регистрация подтверждена - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    def send_thesis_status(self, thesis: Thesis, session: Session) -> None:
        """Ставит в очередь письмо с результатом рассмотрения тезисов (принят/отклонён)."""
        application = thesis.application
        conference = application.conference
        html = render_template(
            'email/thesis_status.html',
            thesis=thesis,
            application=application,
            conference=conference,
            conference_url=self._get_conference_url(conference)
        )
        status_text = "приняты" if thesis.status.value == "accepted" else "отклонены"
        self._send_email(
            subject=f"Тезисы {status_text} - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    def send_conference_reminder(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые напоминания о предстоящей конференции."""
        self._send_to_applications(applications, conference, 'conference_reminder', 'Напоминание о конференции', session)

    def send_schedule_published(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые уведомления о публикации расписания."""
        self._send_to_applications(applications, conference, 'schedule_published', 'Опубликовано расписание', session)

    def send_conference_updated(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые уведомления об изменении данных конференции."""
        self._send_to_applications(applications, conference, 'conference_update', 'Изменения в конференции', session)

    def send_schedule_updated(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые уведомления об изменении расписания."""
        self._send_to_applications(applications, conference, 'schedule_update', 'Изменения в расписании', session)

    def _get_conference_url(self, conference: Conference) -> str:
        """Генерирует внешний URL страницы конференции."""
        return url_for('conference.show_conference', conf_id=conference.id, _external=True)

    def _send_email(
        self, subject: str, recipient: str, html_body: str, queue_type: QueueType, session: Session
    ) -> None:
        """Добавляет одно письмо в очередь."""
        self.__email_queue.enqueue(
            subject=subject,
            recipient=recipient,
            html_body=html_body,
            queue_type=queue_type,
            session=session
        )

    def _send_to_applications(
        self,
        applications: list[Application] | None,
        conference: Conference,
        template_name: str,
        subject_prefix: str,
        session: Session,
        **template_kwargs: Any
    ) -> None:
        """Рассылает письмо по шаблону всем участникам из списка."""
        if not applications:
            return

        conference_url = self._get_conference_url(conference)
        for app in applications:
            html = render_template(
                f'email/{template_name}.html',
                application=app,
                conference=conference,
                conference_url=conference_url,
                **template_kwargs
            )
            self._send_email(
                subject=f"{subject_prefix} - {conference.title}",
                recipient=app.email,
                html_body=html,
                queue_type=QueueType.MASS,
                session=session
            )
