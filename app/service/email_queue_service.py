from app.models.email_queue import EmailQueue, EmailStatus
from app.repository.email_repository import EmailRepository


class EmailQueueService:
    def __init__(self, email_repository: EmailRepository):
        self.__repo = email_repository

    def enqueue(self, subject, recipient, html_body, queue_type, session):
        email = EmailQueue(
            subject=subject,
            recipient=recipient,
            html_body=html_body,
            queue_type=queue_type
        )
        self.__repo.save(email, session)

    def fetch_pending(self, limit, queue_type, session):
        return self.__repo.get_pending_with_limit(limit, queue_type, session)

    def mark_sending(self, email, session):
        self.__repo.add_to_session(session, email)
        email.status = EmailStatus.SENDING

    def mark_completed(self, email: EmailQueue, session):
        self.__repo.add_to_session(session, email)
        email.status = EmailStatus.COMPLETED

    def mark_failed(self, email: EmailQueue, session):
        self.__repo.add_to_session(session, email)
        email.attempts += 1
        if email.attempts == 3:
            email.status = EmailStatus.FAILED
