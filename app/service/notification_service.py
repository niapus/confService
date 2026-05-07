from typing import List, Optional, Any

from flask import url_for, render_template
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.conference import Conference
from app.models.email_queue import QueueType
from app.models.thesis import Thesis
from app.service.email_queue_service import EmailQueueService


class NotificationService:
    """Сервис для отправки email-уведомлений.
    
    Предоставляет методы для отправки различных типов уведомлений
    пользователям системы через очередь email-сообщений.
    """
    
    def __init__(self, email_queue: EmailQueueService, mail_enabled: bool, verification_enabled: bool) -> None:
        """Инициализация сервиса уведомлений.
        
        Args:
            email_queue: Сервис очереди email-сообщений
            mail_enabled: Включена ли отправка почты
            verification_enabled: Включена ли верификация email
        """
        self.__email_queue = email_queue
        self.mail_enabled = mail_enabled
        self.verification_enabled = verification_enabled

    def send_verification_email(self, token: str, application: Application, conference: Conference, session: Session) -> None:
        """Отправить email для подтверждения адреса электронной почты.
        
        Args:
            token: Токен подтверждения
            application: Заявка пользователя
            conference: Конференция
            session: Сессия базы данных
        """
        verification_url = url_for('auth.verify_email', token=token, _external=True)
        html = render_template('email/verification.html',
                               application=application,
                               conference=conference,
                               verification_url=verification_url)

        self._send_email(
            subject=f"Подтверждение - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    def send_registration_confirmed(self, application: Application, session: Session) -> None:
        """Отправить email о подтверждении регистрации.
        
        Args:
            application: Заявка пользователя
            session: Сессия базы данных
        """
        conference = application.conference
        conference_url = self._get_conference_url(conference)
        html = render_template('email/registration_confirmed.html',
                               application=application,
                               conference=conference,
                               conference_url=conference_url)

        self._send_email(
            subject=f"Регистрация подтверждена - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    def send_thesis_status(self, thesis: Thesis, session: Session) -> None:
        """Отправить email о статусе тезисов.
        
        Args:
            thesis: Тезисы
            session: Сессия базы данных
        """
        application = thesis.application
        conference = application.conference
        conference_url = self._get_conference_url(conference)
        html = render_template('email/thesis_status.html',
                               thesis=thesis,
                               application=application,
                               conference=conference,
                               conference_url=conference_url)

        status_text = "приняты" if thesis.status.value == "accepted" else "отклонены"

        self._send_email(
            subject=f"Тезисы {status_text} - {conference.title}",
            recipient=application.email,
            html_body=html,
            queue_type=QueueType.INDIVIDUAL,
            session=session
        )

    def send_conference_reminder(self, applications: List[Application], conference: Conference, session: Session) -> None:
        """Отправить напоминание о конференции.
        
        Args:
            applications: Список заявок для отправки
            conference: Конференция
            session: Сессия базы данных
        """
        self._send_to_applications(
            applications=applications,
            conference=conference,
            template_name='conference_reminder',
            subject_prefix='Напоминание о конференции',
            session=session
        )

    def send_schedule_published(self, applications: List[Application], conference: Conference, session: Session) -> None:
        """Отправить уведомление о публикации расписания.
        
        Args:
            applications: Список заявок для отправки
            conference: Конференция
            session: Сессия базы данных
        """
        self._send_to_applications(
            applications=applications,
            conference=conference,
            template_name='schedule_published',
            subject_prefix='Опубликовано расписание',
            session=session
        )

    def send_conference_updated(self, applications: List[Application], conference: Conference, session: Session) -> None:
        """Отправить уведомление об изменениях в конференции.
        
        Args:
            applications: Список заявок для отправки
            conference: Конференция
            session: Сессия базы данных
        """
        self._send_to_applications(
            applications=applications,
            conference=conference,
            template_name='conference_update',
            subject_prefix='Изменения в конференции',
            session=session
        )

    def send_schedule_updated(self, applications: List[Application], conference: Conference, session: Session) -> None:
        """Отправить уведомление об изменениях в расписании.
        
        Args:
            applications: Список заявок для отправки
            conference: Конференция
            session: Сессия базы данных
        """
        self._send_to_applications(
            applications=applications,
            conference=conference,
            template_name='schedule_update',
            subject_prefix='Изменения в расписании',
            session=session
        )

    def _get_conference_url(self, conference: Conference) -> str:
        """Получить URL страницы конференции.
        
        Args:
            conference: Конференция
            
        Returns:
            URL страницы конференции
        """
        return url_for('conference.show_conference', conf_id=conference.id, _external=True)

    def _send_email(self, subject: str, recipient: str, html_body: str, queue_type: QueueType, session: Session) -> None:
        """Добавить письмо для отправки в очередь.
        
        Args:
            subject: Тема письма
            recipient: Email получателя
            html_body: HTML-содержимое письма
            session: Сессия базы данных
        """
        self.__email_queue.enqueue(
            subject=subject,
            recipient=recipient,
            html_body=html_body,
            queue_type=queue_type,
            session=session
        )

    def _send_to_applications(self, applications: Optional[List[Application]], conference: Conference,
                              template_name: str, subject_prefix: str, session: Session,
                              **template_kwargs: Any) -> None:
        """Добавить письма для отправки в очередь.
        
        Args:
            applications: Список заявок для отправки
            conference: Конференция
            template_name: Имя шаблона без расширения
            subject_prefix: Префикс темы письма
            session: Сессия базы данных
            **template_kwargs: Дополнительные параметры для шаблона
        """
        if not applications:
            return

        conference_url = self._get_conference_url(conference)
        for app in applications:
            html = render_template(f'email/{template_name}.html',
                                   application=app,
                                   conference=conference,
                                   conference_url=conference_url,
                                   **template_kwargs)

            self._send_email(
                subject=f"{subject_prefix} - {conference.title}",
                recipient=app.email,
                html_body=html,
                queue_type=QueueType.MASS,
                session=session
            )