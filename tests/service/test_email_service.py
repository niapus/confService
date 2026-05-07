from unittest.mock import MagicMock

import pytest

from app.service.email_service import EmailService


@pytest.fixture
def mock_mailer():
    return MagicMock()


@pytest.fixture
def email_service(mock_mailer):
    return EmailService(mailer=mock_mailer, default_sender="noreply@test.com")


class TestConnect:

    def test_connect_delegates_to_mailer(self, email_service, mock_mailer):
        mock_mailer.connect.return_value = "connection"

        result = email_service.connect()

        mock_mailer.connect.assert_called_once()
        assert result == "connection"


class TestSendSync:

    def test_send_sync_with_default_sender(self, email_service, mock_mailer):
        email_service.send_sync(
            subject="Test",
            recipients=["user@test.com"],
            html_body="<p>Hello</p>"
        )

        mock_mailer.send.assert_called_once_with(
            subject="Test",
            recipients=["user@test.com"],
            html_body="<p>Hello</p>",
            sender="noreply@test.com"
        )

    def test_send_sync_with_custom_sender(self, email_service, mock_mailer):
        email_service.send_sync(
            subject="Test",
            recipients=["user@test.com"],
            html_body="<p>Hello</p>",
            sender="custom@test.com"
        )

        mock_mailer.send.assert_called_once_with(
            subject="Test",
            recipients=["user@test.com"],
            html_body="<p>Hello</p>",
            sender="custom@test.com"
        )
