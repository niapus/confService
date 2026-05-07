from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest

from app.models.email_queue import QueueType
from app.service.async_email_service import AsyncEmailService
from tests.factories import make_email_queue


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def mock_email_service(mock_conn):
    svc = MagicMock()
    @contextmanager
    def mock_connect():
        yield mock_conn
    svc.connect = mock_connect
    return svc


@pytest.fixture
def async_email_service(mock_email_service, mock_email_queue_service):
    return AsyncEmailService(email_service=mock_email_service, email_queue=mock_email_queue_service)


class TestEnabled:

    def test_enabled_when_service_exists(self, async_email_service):
        assert async_email_service.enabled is True

    def test_disabled_when_service_is_none(self, mock_email_queue_service):
        svc = AsyncEmailService(email_service=None, email_queue=mock_email_queue_service)
        assert svc.enabled is False


class TestProcessIndividualQueue:

    def test_process_individual_queue(self, async_email_service, mock_email_queue_service,
                                      mock_email_service, mock_session, mock_conn):
        item = make_email_queue()
        mock_email_queue_service.fetch_pending.return_value = [item]

        with patch('app.service.async_email_service.database') as mock_db, \
             patch('app.service.async_email_service.Message') as MockMsg:
            mock_session_obj = MagicMock()
            mock_db.Session.return_value = mock_session_obj

            sent, failed = async_email_service.process_individual_queue()

        mock_email_queue_service.fetch_pending.assert_called_once_with(
            10, QueueType.INDIVIDUAL, mock_session_obj
        )

    def test_process_returns_zero_when_disabled(self, mock_email_queue_service):
        svc = AsyncEmailService(email_service=None, email_queue=mock_email_queue_service)

        sent, failed = svc.process_individual_queue()
        assert sent == 0
        assert failed == 0


class TestProcessMassQueue:

    def test_process_mass_queue(self, async_email_service, mock_email_queue_service,
                                 mock_email_service, mock_conn):
        item = make_email_queue(queue_type=QueueType.MASS)
        mock_email_queue_service.fetch_pending.return_value = [item]

        with patch('app.service.async_email_service.database') as mock_db, \
             patch('app.service.async_email_service.Message') as MockMsg:
            mock_session_obj = MagicMock()
            mock_db.Session.return_value = mock_session_obj

            sent, failed = async_email_service.process_mass_queue()

        mock_email_queue_service.fetch_pending.assert_called_once_with(
            30, QueueType.MASS, mock_session_obj
        )


class TestProcessQueue:

    def test_returns_zero_when_no_items(self, async_email_service, mock_email_queue_service):
        mock_email_queue_service.fetch_pending.return_value = []

        with patch('app.service.async_email_service.database') as mock_db:
            mock_session_obj = MagicMock()
            mock_db.Session.return_value = mock_session_obj

            sent, failed = async_email_service.process_individual_queue()

        assert sent == 0
        assert failed == 0

    def test_sends_items_successfully(self, async_email_service, mock_email_queue_service,
                                       mock_email_service, mock_conn):
        item1 = make_email_queue(eq_id=1, subject="Sub1", recipient="r1@test.com", html_body="<p>1</p>")
        item2 = make_email_queue(eq_id=2, subject="Sub2", recipient="r2@test.com", html_body="<p>2</p>")
        mock_email_queue_service.fetch_pending.return_value = [item1, item2]

        with patch('app.service.async_email_service.database') as mock_db, \
             patch('app.service.async_email_service.Message') as MockMsg:
            mock_session_obj = MagicMock()
            mock_db.Session.return_value = mock_session_obj

            sent, failed = async_email_service.process_individual_queue()

        assert sent == 2
        assert failed == 0
        assert mock_conn.send.call_count == 2

    def test_handles_send_failure(self, async_email_service, mock_email_queue_service,
                                   mock_email_service, mock_conn):
        item = make_email_queue()
        mock_email_queue_service.fetch_pending.return_value = [item]
        mock_conn.send.side_effect = Exception("SMTP error")

        with patch('app.service.async_email_service.database') as mock_db, \
             patch('app.service.async_email_service.Message') as MockMsg:
            mock_session_obj = MagicMock()
            mock_db.Session.return_value = mock_session_obj

            sent, failed = async_email_service.process_individual_queue()

        assert sent == 0
        assert failed == 1
        mock_email_queue_service.mark_failed.assert_called_once()

    def test_mixed_success_and_failure(self, async_email_service, mock_email_queue_service,
                                        mock_email_service, mock_conn):
        item1 = make_email_queue(eq_id=1)
        item2 = make_email_queue(eq_id=2)
        mock_email_queue_service.fetch_pending.return_value = [item1, item2]

        call_count = [0]
        def side_effect(msg):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("SMTP error")

        mock_conn.send.side_effect = side_effect

        with patch('app.service.async_email_service.database') as mock_db, \
             patch('app.service.async_email_service.Message') as MockMsg:
            mock_session_obj = MagicMock()
            mock_db.Session.return_value = mock_session_obj

            sent, failed = async_email_service.process_individual_queue()

        assert sent == 1
        assert failed == 1
