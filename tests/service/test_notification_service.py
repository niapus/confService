from unittest.mock import patch

import pytest

from app.models.email_queue import QueueType
from app.models.thesis import ThesisStatus
from app.service.notification_service import NotificationService
from tests.factories import make_conference, make_application, make_thesis


@pytest.fixture
def notification_service(mock_email_queue_service):
    return NotificationService(
        email_queue=mock_email_queue_service,
        mail_enabled=True,
        verification_enabled=True
    )


@pytest.fixture
def notification_service_no_mail(mock_email_queue_service):
    return NotificationService(
        email_queue=mock_email_queue_service,
        mail_enabled=False,
        verification_enabled=False
    )


class TestInit:

    def test_init_properties(self, notification_service):
        assert notification_service.mail_enabled is True
        assert notification_service.verification_enabled is True


class TestSendVerificationEmail:

    @patch('app.service.notification_service.render_template', return_value='<html>verify</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/verify?token=abc')
    def test_send_verification_email(self, mock_url_for, mock_render, notification_service,
                                      mock_email_queue_service, mock_session):
        app = make_application()
        conf = make_conference()

        notification_service.send_verification_email("abc", app, conf, mock_session)

        mock_email_queue_service.enqueue.assert_called_once()
        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert call_kwargs['recipient'] == app.email
        assert call_kwargs['queue_type'] == QueueType.INDIVIDUAL
        assert "Подтверждение" in call_kwargs['subject']


class TestSendRegistrationConfirmed:

    @patch('app.service.notification_service.render_template', return_value='<html>confirmed</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_registration_confirmed(self, mock_url_for, mock_render, notification_service,
                                          mock_email_queue_service, mock_session):
        app = make_application()
        conf = make_conference()
        app.conference = conf

        notification_service.send_registration_confirmed(app, mock_session)

        mock_email_queue_service.enqueue.assert_called_once()
        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert call_kwargs['recipient'] == app.email
        assert call_kwargs['queue_type'] == QueueType.INDIVIDUAL
        assert "Регистрация подтверждена" in call_kwargs['subject']


class TestSendThesisStatus:

    @patch('app.service.notification_service.render_template', return_value='<html>thesis</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_thesis_accepted(self, mock_url_for, mock_render, notification_service,
                                   mock_email_queue_service, mock_session):
        thesis = make_thesis(status=ThesisStatus.ACCEPTED)
        app = make_application()
        conf = make_conference()
        app.conference = conf
        thesis.application = app

        notification_service.send_thesis_status(thesis, mock_session)

        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert "приняты" in call_kwargs['subject']

    @patch('app.service.notification_service.render_template', return_value='<html>thesis</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_thesis_rejected(self, mock_url_for, mock_render, notification_service,
                                   mock_email_queue_service, mock_session):
        thesis = make_thesis(status=ThesisStatus.REJECTED)
        app = make_application()
        conf = make_conference()
        app.conference = conf
        thesis.application = app

        notification_service.send_thesis_status(thesis, mock_session)

        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert "отклонены" in call_kwargs['subject']


class TestSendConferenceReminder:

    @patch('app.service.notification_service.render_template', return_value='<html>reminder</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_conference_reminder(self, mock_url_for, mock_render, notification_service,
                                       mock_email_queue_service, mock_session):
        app1 = make_application(app_id=1, email="a@test.com")
        app2 = make_application(app_id=2, email="b@test.com")
        conf = make_conference()

        notification_service.send_conference_reminder([app1, app2], conf, mock_session)

        assert mock_email_queue_service.enqueue.call_count == 2
        for c in mock_email_queue_service.enqueue.call_args_list:
            assert c[1]['queue_type'] == QueueType.MASS
            assert "Напоминание" in c[1]['subject']

    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_conference_reminder_empty_list(self, mock_url_for, notification_service,
                                                  mock_email_queue_service, mock_session):
        conf = make_conference()

        notification_service.send_conference_reminder([], conf, mock_session)

        mock_email_queue_service.enqueue.assert_not_called()

    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_conference_reminder_none_list(self, mock_url_for, notification_service,
                                                 mock_email_queue_service, mock_session):
        conf = make_conference()

        notification_service.send_conference_reminder(None, conf, mock_session)

        mock_email_queue_service.enqueue.assert_not_called()


class TestSendSchedulePublished:

    @patch('app.service.notification_service.render_template', return_value='<html>schedule</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_schedule_published(self, mock_url_for, mock_render, notification_service,
                                      mock_email_queue_service, mock_session):
        app = make_application()
        conf = make_conference()

        notification_service.send_schedule_published([app], conf, mock_session)

        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert "Опубликовано расписание" in call_kwargs['subject']
        assert call_kwargs['queue_type'] == QueueType.MASS


class TestSendConferenceUpdated:

    @patch('app.service.notification_service.render_template', return_value='<html>update</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_conference_updated(self, mock_url_for, mock_render, notification_service,
                                      mock_email_queue_service, mock_session):
        app = make_application()
        conf = make_conference()

        notification_service.send_conference_updated([app], conf, mock_session)

        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert "Изменения в конференции" in call_kwargs['subject']


class TestSendScheduleUpdated:

    @patch('app.service.notification_service.render_template', return_value='<html>update</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_send_schedule_updated(self, mock_url_for, mock_render, notification_service,
                                    mock_email_queue_service, mock_session):
        app = make_application()
        conf = make_conference()

        notification_service.send_schedule_updated([app], conf, mock_session)

        call_kwargs = mock_email_queue_service.enqueue.call_args[1]
        assert "Изменения в расписании" in call_kwargs['subject']


class TestSendEmail:

    def test_send_email_enqueues(self, notification_service, mock_email_queue_service, mock_session):
        notification_service._send_email(
            subject="Test",
            recipient="test@test.com",
            html_body="<p>Test</p>",
            queue_type=QueueType.INDIVIDUAL,
            session=mock_session
        )

        mock_email_queue_service.enqueue.assert_called_once_with(
            subject="Test",
            recipient="test@test.com",
            html_body="<p>Test</p>",
            queue_type=QueueType.INDIVIDUAL,
            session=mock_session
        )


class TestSendToApplications:

    @patch('app.service.notification_service.render_template', return_value='<html>test</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_sends_to_each_application(self, mock_url_for, mock_render, notification_service,
                                        mock_email_queue_service, mock_session):
        app1 = make_application(app_id=1, email="a@test.com")
        app2 = make_application(app_id=2, email="b@test.com")
        conf = make_conference()

        notification_service._send_to_applications(
            applications=[app1, app2],
            conference=conf,
            template_name='test_template',
            subject_prefix='Test Prefix',
            session=mock_session
        )

        assert mock_email_queue_service.enqueue.call_count == 2

    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_skips_when_applications_empty(self, mock_url_for, notification_service,
                                            mock_email_queue_service, mock_session):
        conf = make_conference()

        notification_service._send_to_applications(
            applications=[],
            conference=conf,
            template_name='test_template',
            subject_prefix='Test',
            session=mock_session
        )

        mock_email_queue_service.enqueue.assert_not_called()

    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_skips_when_applications_none(self, mock_url_for, notification_service,
                                           mock_email_queue_service, mock_session):
        conf = make_conference()

        notification_service._send_to_applications(
            applications=None,
            conference=conf,
            template_name='test_template',
            subject_prefix='Test',
            session=mock_session
        )

        mock_email_queue_service.enqueue.assert_not_called()

    @patch('app.service.notification_service.render_template', return_value='<html>test</html>')
    @patch('app.service.notification_service.url_for', return_value='http://localhost/conf/1')
    def test_passes_template_kwargs(self, mock_url_for, mock_render, notification_service,
                                     mock_email_queue_service, mock_session):
        app = make_application()
        conf = make_conference()

        notification_service._send_to_applications(
            applications=[app],
            conference=conf,
            template_name='test_template',
            subject_prefix='Test',
            session=mock_session,
            extra_key='extra_value'
        )

        mock_render.assert_called_once()
        render_kwargs = mock_render.call_args[1]
        assert render_kwargs.get('extra_key') == 'extra_value'
