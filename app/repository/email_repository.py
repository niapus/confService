from app.models.email_queue import EmailQueue, EmailStatus, QueueType


class EmailRepository:
    def save(self, email: EmailQueue, session):
        session.add(email)

    def get_pending_with_limit(self, limit, queue_type: QueueType, session):
        return session.query(EmailQueue)\
            .filter(EmailQueue.status == EmailStatus.PENDING, EmailQueue.queue_type == queue_type)\
            .order_by(EmailQueue.created_at)\
            .limit(limit)\
            .all()

    def add_to_session(self, session, email: EmailQueue):
        session.add(email)