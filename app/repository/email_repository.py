from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.email_queue import EmailQueue, EmailStatus, QueueType


class EmailRepository:
    """Доступ к данным очереди исходящих писем."""

    def save(self, email: EmailQueue, session: Session) -> None:
        session.add(email)

    def delete(self, email: EmailQueue, session: Session) -> None:
        session.delete(email)

    def delete_failed_older_than(self, days: int, session: Session) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        return session.query(EmailQueue).filter(
            EmailQueue.status == EmailStatus.FAILED,
            EmailQueue.created_at < cutoff
        ).delete(synchronize_session=False)

    def get_pending_with_limit(
        self, limit: int, queue_type: QueueType, session: Session
    ) -> list[EmailQueue]:
        return session.query(EmailQueue)\
            .filter(EmailQueue.status == EmailStatus.PENDING, EmailQueue.queue_type == queue_type)\
            .order_by(EmailQueue.created_at)\
            .limit(limit)\
            .all()