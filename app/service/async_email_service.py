import logging
import socket

from flask_mail import Message

from app.core import database
from app.models.email_queue import QueueType
from app.service.email_queue_service import EmailQueueService
from app.service.email_service import EmailService

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 10


class AsyncEmailService:
    """Фоновая обработка очереди исходящих писем через SMTP."""

    def __init__(self, email_service: EmailService, email_queue: EmailQueueService) -> None:
        self._email_service = email_service
        self._email_queue = email_queue

    @property
    def enabled(self) -> bool:
        """True если SMTP-сервис настроен и доступен."""
        return self._email_service is not None

    def process_individual_queue(self) -> tuple[int, int]:
        """Обрабатывает до 10 индивидуальных писем из очереди. Возвращает (sent, failed)."""
        return self._process_queue(10, QueueType.INDIVIDUAL)

    def process_mass_queue(self) -> tuple[int, int]:
        """Обрабатывает до 30 массовых писем из очереди. Возвращает (sent, failed)."""
        return self._process_queue(30, QueueType.MASS)

    def _process_queue(self, limit: int, queue_type: QueueType) -> tuple[int, int]:
        """Забирает письма из очереди и отправляет через SMTP.

        Args:
            limit: Максимальное количество писем, обрабатываемых за один вызов.

        Returns:
            Кортеж ``(sent, failed)`` — количество отправленных и упавших писем.
        """
        if not self.enabled:
            return 0, 0

        session = database.Session()
        try:
            items = self._email_queue.fetch_pending(limit, queue_type, session)
        finally:
            session.close()

        if not items:
            return 0, 0

        sent = 0
        failed = 0

        prev_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(SMTP_TIMEOUT)
        try:
            conn_ctx = self._email_service.connect()
            conn = conn_ctx.__enter__()
        except Exception as e:
            socket.setdefaulttimeout(prev_timeout)
            logger.warning(f"SMTP подключение не удалось: {e}")
            return 0, 0

        try:
            for item in items:
                try:
                    msg = Message(
                        subject=item.subject,
                        recipients=[item.recipient],
                        html=item.html_body
                    )
                    conn.send(msg)
                except Exception as e:
                    session = database.Session()
                    try:
                        self._email_queue.mark_failed(item, session)
                        session.commit()
                        failed += 1
                    finally:
                        session.close()
                    continue

                session = database.Session()
                try:
                    self._email_queue.mark_completed(item, session)
                    session.commit()
                    sent += 1
                finally:
                    session.close()
        finally:
            conn_ctx.__exit__(None, None, None)
            socket.setdefaulttimeout(prev_timeout)

        return sent, failed
