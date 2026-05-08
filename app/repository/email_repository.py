from sqlalchemy.orm import Session

from app.models.email_queue import EmailQueue, EmailStatus, QueueType


class EmailRepository:
    """Доступ к данным очереди исходящих писем."""

    def save(self, email: EmailQueue, session: Session) -> None:
        session.add(email)

    def get_pending_with_limit(
        self, limit: int, queue_type: QueueType, session: Session
    ) -> list[EmailQueue]:
        return session.query(EmailQueue)\
            .filter(EmailQueue.status == EmailStatus.PENDING, EmailQueue.queue_type == queue_type)\
            .order_by(EmailQueue.created_at)\
            .limit(limit)\
            .all()