import pytest

from app.models.email_queue import EmailStatus, QueueType
from app.service.email_queue_service import EmailQueueService
from tests.factories import make_email_queue


@pytest.fixture
def email_queue_service(mock_email_repository):
    return EmailQueueService(mock_email_repository)


class TestEnqueue:

    def test_enqueue_creates_email(self, email_queue_service, mock_email_repository, mock_session):
        email_queue_service.enqueue(
            subject="Test Subject",
            recipient="test@test.com",
            html_body="<p>Test</p>",
            queue_type=QueueType.INDIVIDUAL,
            session=mock_session
        )

        mock_email_repository.save.assert_called_once()
        email = mock_email_repository.save.call_args[0][0]
        assert email.subject == "Test Subject"
        assert email.recipient == "test@test.com"
        assert email.html_body == "<p>Test</p>"
        assert email.queue_type == QueueType.INDIVIDUAL


class TestFetchPending:

    def test_fetch_pending(self, email_queue_service, mock_email_repository, mock_session):
        mock_email_repository.get_pending_with_limit.return_value = ["item1"]

        result = email_queue_service.fetch_pending(10, QueueType.INDIVIDUAL, mock_session)

        mock_email_repository.get_pending_with_limit.assert_called_once_with(
            10, QueueType.INDIVIDUAL, mock_session
        )
        assert result == ["item1"]


class TestDelete:

    def test_delete(self, email_queue_service, mock_email_repository, mock_session):
        eq = make_email_queue()

        email_queue_service.delete(eq, mock_session)

        mock_email_repository.delete.assert_called_once_with(eq, mock_session)


class TestMarkFailed:

    def test_mark_failed_increments_attempts(self, email_queue_service, mock_email_repository, mock_session):
        eq = make_email_queue(attempts=0)

        email_queue_service.mark_failed(eq, mock_session)

        assert eq.attempts == 1
        assert eq.status != EmailStatus.FAILED
        mock_email_repository.save.assert_called_once_with(eq, mock_session)

    def test_mark_failed_sets_failed_after_3_attempts(self, email_queue_service, mock_email_repository, mock_session):
        eq = make_email_queue(attempts=2)

        email_queue_service.mark_failed(eq, mock_session)

        assert eq.attempts == 3
        assert eq.status == EmailStatus.FAILED

    def test_mark_failed_does_not_set_failed_before_3(self, email_queue_service, mock_email_repository, mock_session):
        eq = make_email_queue(attempts=1)

        email_queue_service.mark_failed(eq, mock_session)

        assert eq.attempts == 2
        assert eq.status != EmailStatus.FAILED
