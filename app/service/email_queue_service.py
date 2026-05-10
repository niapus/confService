from sqlalchemy.orm import Session

from app.models.email_queue import EmailQueue, EmailStatus, QueueType
from app.repository.email_repository import EmailRepository


class EmailQueueService:
    """Управление очередью исходящих писем: постановка в очередь и смена статусов."""

    def __init__(self, email_repository: EmailRepository) -> None:
        self.__repo = email_repository

    def enqueue(
        self, subject: str, recipient: str, html_body: str, queue_type: QueueType, session: Session
    ) -> None:
        """Создаёт запись письма в очереди со статусом PENDING."""
        email = EmailQueue(
            subject=subject,
            recipient=recipient,
            html_body=html_body,
            queue_type=queue_type
        )
        self.__repo.save(email, session)

    def fetch_pending(self, limit: int, queue_type: QueueType, session: Session) -> list[EmailQueue]:
        """Возвращает до limit писем со статусом PENDING из указанной очереди."""
        return self.__repo.get_pending_with_limit(limit, queue_type, session)

    def delete(self, email: EmailQueue, session: Session) -> None:
        """Удаляет письмо из очереди после успешной отправки."""
        self.__repo.delete(email, session)

    def mark_failed(self, email: EmailQueue, session: Session) -> None:
        """Увеличивает счётчик попыток. После 3 неудач переводит письмо в статус FAILED."""
        email.attempts += 1
        if email.attempts == 3:
            email.status = EmailStatus.FAILED
        self.__repo.save(email, session)

    def cleanup_failed(self, days: int, session: Session) -> int:
        """Удаляет FAILED письма старше указанного количества дней."""
        return self.__repo.delete_failed_older_than(days, session)
