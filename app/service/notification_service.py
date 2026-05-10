from flask import url_for, render_template, current_app
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.conference import Conference
from app.models.email_queue import QueueType
from app.models.thesis import Thesis, ThesisStatus
from app.service.email_queue_service import EmailQueueService


def _require_mail(func):
    """Декоратор: пропускает выполнение метода если почта отключена."""
    def wrapper(self, *args, **kwargs):
        if not self.mail_enabled:
            return
        return func(self, *args, **kwargs)
    return wrapper


class NotificationService:
    """Отправка email-уведомлений участникам через очередь писем."""

    def __init__(
        self, email_queue: EmailQueueService, mail_enabled: bool, verification_enabled: bool
    ) -> None:
        self.__email_queue = email_queue
        self.mail_enabled = mail_enabled
        self.verification_enabled = verification_enabled

    @_require_mail
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

    @_require_mail
    def send_registration_confirmed(self, application: Application, session: Session) -> None:
        """Ставит в очередь письмо об успешном подтверждении регистрации."""
        conference = application.conference
        conference_url = self._get_conference_url(conference)
        html = render_template(
            'email/email.html',
            header='Регистрация подтверждена',
            mail_text='Ваша регистрация на конференцию успешно подтверждена.',
            application=application,
            conference=conference,
            button_url=conference_url,
            button_text='Перейти к конференции'
        )
        self._send_email(
            subject=f"Регистрация подтверждена - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    @_require_mail
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
        status_text = "приняты" if thesis.status == ThesisStatus.ACCEPTED else "отклонены"
        self._send_email(
            subject=f"Тезисы {status_text} - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    @_require_mail
    def send_conference_reminder(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые напоминания о предстоящей конференции."""
        self._send_to_applications(
            applications, conference,
            header='Напоминание о конференции',
            mail_text='Напоминаем о предстоящей конференции.',
            subject_prefix='Напоминание о конференции',
            session=session
        )

    @_require_mail
    def send_schedule_published(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые уведомления о публикации расписания."""
        self._send_to_applications(
            applications, conference,
            header='Опубликовано расписание',
            mail_text='Опубликовано расписание конференции.',
            subject_prefix='Опубликовано расписание',
            session=session
        )

    @_require_mail
    def send_conference_updated(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые уведомления об изменении данных конференции."""
        self._send_to_applications(
            applications, conference,
            header='Изменения в конференции',
            mail_text='Произошли изменения в данных конференции.',
            subject_prefix='Изменения в конференции',
            session=session
        )

    @_require_mail
    def send_schedule_updated(
        self, applications: list[Application], conference: Conference, session: Session
    ) -> None:
        """Ставит в очередь массовые уведомления об изменении расписания."""
        self._send_to_applications(
            applications, conference,
            header='Изменения в расписании',
            mail_text='Произошли изменения в расписании конференции.',
            subject_prefix='Изменения в расписании',
            session=session
        )

    def _get_conference_url(self, conference: Conference) -> str:
        base_url = current_app.config.get('BASE_URL', '').rstrip('/')
        return f"{base_url}/conference/{conference.id}"

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
        header: str,
        mail_text: str,
        subject_prefix: str,
        session: Session,
        button_url: str | None = None,
        button_text: str | None = None
    ) -> None:
        """Рассылает письмо по универсальному шаблону всем участникам из списка."""
        if not applications:
            return

        conference_url = self._get_conference_url(conference)
        for app in applications:
            html = render_template(
                'email/email.html',
                header=header,
                mail_text=mail_text,
                application=app,
                conference=conference,
                button_url=button_url or conference_url,
                button_text=button_text or 'Перейти к конференции'
            )
            self._send_email(
                subject=f"{subject_prefix} - {conference.title}",
                recipient=app.email,
                html_body=html,
                queue_type=QueueType.MASS,
                session=session
            )
