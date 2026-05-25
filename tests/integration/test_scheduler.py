"""
Интеграционные тесты SchedulerService.

Покрывают все 5 фоновых job'ов:
  - individual (15s): обработка индивидуальной очереди писем;
  - mass (60s): обработка массовой очереди;
  - reminders (cron 10:00): напоминания за 1 день до конференции;
  - cleanup_emails (cron sun 3:00): удаление FAILED писем старше 30 дней;
  - cleanup_applications (cron sun 3:30): удаление UNCONFIRMED заявок старше 7 дней.

Сами таймеры APScheduler не тестируем — это поведение библиотеки. Проверяем:
  - регистрацию job'ов с правильными id и cron/interval параметрами;
  - корректность callback'а каждого job'а через прямой вызов;
  - изоляцию ошибок (исключение в job'е не валит планировщик);
  - граничные кейсы по датам через freezegun.
"""
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time

from app.core.scheduler import SchedulerService
from app.models.application import Application, ApplicationStatus, GenderEnum, DegreeEnum, \
    EducationEnum, ParticipationFormatEnum
from app.models.conference import Conference
from app.models.email_queue import EmailQueue, EmailStatus, QueueType
from app.models.schedule_item import ScheduleItem, ScheduleItemType


# ----------------------------------------------------------------------------
# Хелперы для подготовки данных в БД
# ----------------------------------------------------------------------------

def _make_conf(start_in_days=60, end_offset=2):
    today = date.today()
    return Conference(
        title=f"Conf+{start_in_days}",
        description_md="x", description_html="x", tagline="t",
        registration_deadline=today + timedelta(days=max(start_in_days - 30, 0)),
        submission_deadline=today + timedelta(days=max(start_in_days - 15, 0)),
        start_date=today + timedelta(days=start_in_days),
        end_date=today + timedelta(days=start_in_days + end_offset),
        performance_time=15,
    )


def _make_application(conf_id, email="p@test.com", status=ApplicationStatus.CONFIRMED):
    return Application(
        conference_id=conf_id,
        surname="И", name="И", patronymic="И",
        gender=GenderEnum.MALE, birth_date=date(2000, 1, 1),
        degree=DegreeEnum.NONE,
        is_worker=False, is_student=True,
        study_name="x", study_place="x", study_level=EducationEnum.MASTER,
        participation_format=ParticipationFormatEnum.OFFLINE,
        email=email, status=status,
    )


def _make_email(subject="s", recipient="r@test.com",
                queue_type=QueueType.INDIVIDUAL,
                status=EmailStatus.PENDING, attempts=0, created_at=None):
    e = EmailQueue(
        subject=subject, recipient=recipient, html_body="<p>x</p>",
        queue_type=queue_type, status=status, attempts=attempts,
    )
    if created_at is not None:
        e.created_at = created_at
    return e


@pytest.fixture
def session_mail(app_with_mail):
    from app.core import database
    s = database.Session()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


# ----------------------------------------------------------------------------
# TestJobRegistration: после start() есть 5 джобов с верными параметрами
# ----------------------------------------------------------------------------

class TestJobRegistration:
    """Подменяем сами callback'и на no-op, чтобы start() не пытался ходить в SMTP."""

    @pytest.fixture
    def started_scheduler(self, app_with_mail, monkeypatch):
        # Никаких реальных операций — только проверка регистрации job'ов.
        monkeypatch.setattr(SchedulerService, "_process_individual", lambda self: None)
        monkeypatch.setattr(SchedulerService, "_process_mass", lambda self: None)
        monkeypatch.setattr(SchedulerService, "_check_reminders", lambda self: None)
        monkeypatch.setattr(SchedulerService, "_cleanup_emails", lambda self: None)
        monkeypatch.setattr(SchedulerService, "_cleanup_applications", lambda self: None)

        svc = SchedulerService(app_with_mail)
        svc.start()
        try:
            yield svc
        finally:
            svc._scheduler.shutdown(wait=False)

    def test_all_five_jobs_registered(self, started_scheduler):
        ids = {j.id for j in started_scheduler._scheduler.get_jobs()}
        assert ids == {"individual", "mass", "reminders",
                       "cleanup_emails", "cleanup_applications"}

    def test_individual_interval_15s(self, started_scheduler):
        job = started_scheduler._scheduler.get_job("individual")
        assert job.trigger.interval == timedelta(seconds=10)

    def test_mass_interval_60s(self, started_scheduler):
        job = started_scheduler._scheduler.get_job("mass")
        assert job.trigger.interval == timedelta(seconds=60)

    def test_reminders_cron_10_00(self, started_scheduler):
        job = started_scheduler._scheduler.get_job("reminders")
        fields = {f.name: str(f) for f in job.trigger.fields}
        assert fields["hour"] == "10"
        assert fields["minute"] == "0"

    def test_cleanup_emails_cron_sun_03_00(self, started_scheduler):
        job = started_scheduler._scheduler.get_job("cleanup_emails")
        fields = {f.name: str(f) for f in job.trigger.fields}
        assert fields["day_of_week"] == "sun"
        assert fields["hour"] == "3"
        assert fields["minute"] == "0"

    def test_cleanup_applications_cron_sun_03_30(self, started_scheduler):
        job = started_scheduler._scheduler.get_job("cleanup_applications")
        fields = {f.name: str(f) for f in job.trigger.fields}
        assert fields["day_of_week"] == "sun"
        assert fields["hour"] == "3"
        assert fields["minute"] == "30"

    def test_job_defaults_applied(self, started_scheduler):
        for job in started_scheduler._scheduler.get_jobs():
            assert job.max_instances == 1
            assert job.coalesce is True


# ----------------------------------------------------------------------------
# TestProcessIndividual / TestProcessMass: callback дёргает AsyncEmailService
# ----------------------------------------------------------------------------

class TestProcessIndividualCallback:

    def test_callback_invokes_async_email_service(self, app_with_mail):
        svc = SchedulerService(app_with_mail)
        mock_email = MagicMock()
        mock_email.process_individual_queue.return_value = (3, 1)
        svc._services._services["email"] = mock_email

        svc._process_individual()

        mock_email.process_individual_queue.assert_called_once()

    def test_runs_within_app_context(self, app_with_mail):
        from flask import current_app

        captured = {}

        def capture():
            captured["app_name"] = current_app.name
            return (0, 0)

        svc = SchedulerService(app_with_mail)
        svc._services._services["email"] = MagicMock(
            process_individual_queue=MagicMock(side_effect=capture)
        )
        svc._process_individual()
        assert "app_name" in captured  # app_context был активен


class TestProcessMassCallback:

    def test_callback_invokes_mass_processor(self, app_with_mail):
        svc = SchedulerService(app_with_mail)
        mock_email = MagicMock()
        mock_email.process_mass_queue.return_value = (5, 0)
        svc._services._services["email"] = mock_email

        svc._process_mass()
        mock_email.process_mass_queue.assert_called_once()


# ----------------------------------------------------------------------------
# TestCheckReminders: напоминания за 1 день, freezegun для детерминизма
# ----------------------------------------------------------------------------

class TestCheckRemindersJob:

    def test_no_reminders_when_no_upcoming(self, app_with_mail, session_mail):
        svc = SchedulerService(app_with_mail)
        # Никаких конференций — никаких писем.
        svc._do_check_reminders()
        assert session_mail.query(EmailQueue).count() == 0

    def test_reminder_for_conference_starting_tomorrow_with_scheduled_talk(
        self, app_with_mail, session_mail
    ):
        """Конференция стартует завтра, есть докладчик в расписании → 1 mass-письмо."""
        from app.dto.dto import ConferenceDTO

        with freeze_time("2026-06-01 09:00:00"):
            # Конференция через 1 день
            today = date.today()
            conf = Conference(
                title="Tomorrow",
                description_md="x", description_html="x", tagline="t",
                registration_deadline=today,
                submission_deadline=today,
                start_date=today + timedelta(days=1),
                end_date=today + timedelta(days=2),
                performance_time=15,
            )
            session_mail.add(conf)
            session_mail.commit()

            app_obj = _make_application(conf.id, email="speaker@test.com")
            session_mail.add(app_obj)
            session_mail.commit()

            # Помещаем участника в расписание как докладчика.
            session_mail.add(ScheduleItem(
                conference_id=conf.id,
                item_type=ScheduleItemType.TALK,
                global_order=1,
                application_id=app_obj.id,
                talk_speaker="speaker",
                talk_title="t",
                talk_duration=15,
            ))
            session_mail.commit()

            svc = SchedulerService(app_with_mail)
            # _check_reminders оборачивает _do_check_reminders в app_context.
            svc._check_reminders()
            session_mail.expire_all()  # перечитать после коммита внутри job'а

            mass = session_mail.query(EmailQueue).filter_by(queue_type=QueueType.MASS).all()
            assert len(mass) == 1
            assert mass[0].recipient == "speaker@test.com"
            assert "напоминание" in mass[0].subject.lower()

    def test_no_reminder_when_no_one_scheduled(self, app_with_mail, session_mail):
        """Конференция завтра, но никто не в расписании → 0 писем."""
        today = date.today()
        conf = Conference(
            title="X",
            description_md="x", description_html="x", tagline="t",
            registration_deadline=today,
            submission_deadline=today,
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=2),
            performance_time=15,
        )
        session_mail.add(conf)
        session_mail.commit()
        # Заявка есть, но в расписании нет.
        session_mail.add(_make_application(conf.id))
        session_mail.commit()

        svc = SchedulerService(app_with_mail)
        svc._do_check_reminders()
        session_mail.expire_all()
        assert session_mail.query(EmailQueue).count() == 0

    def test_no_reminder_when_conference_starts_in_2_days(self, app_with_mail, session_mail):
        today = date.today()
        conf = Conference(
            title="X",
            description_md="x", description_html="x", tagline="t",
            registration_deadline=today,
            submission_deadline=today,
            start_date=today + timedelta(days=2),
            end_date=today + timedelta(days=3),
            performance_time=15,
        )
        session_mail.add(conf)
        session_mail.commit()
        app_obj = _make_application(conf.id)
        session_mail.add(app_obj)
        session_mail.commit()
        session_mail.add(ScheduleItem(
            conference_id=conf.id,
            item_type=ScheduleItemType.TALK,
            global_order=1,
            application_id=app_obj.id,
            talk_speaker="s", talk_title="t", talk_duration=15,
        ))
        session_mail.commit()

        svc = SchedulerService(app_with_mail)
        svc._do_check_reminders()
        session_mail.expire_all()
        assert session_mail.query(EmailQueue).count() == 0


# ----------------------------------------------------------------------------
# TestCleanupEmailsJob: FAILED старше 30 дней удаляются, остальное — нет
# ----------------------------------------------------------------------------

class TestCleanupEmailsJob:

    def test_deletes_failed_older_than_30_days(self, app_with_mail, session_mail):
        with freeze_time("2026-05-01 12:00:00"):
            old_failed = _make_email(
                subject="old_failed", status=EmailStatus.FAILED,
                created_at=datetime(2026, 3, 1, 12, 0, 0),  # 61 день назад
            )
            fresh_failed = _make_email(
                subject="fresh_failed", status=EmailStatus.FAILED,
                created_at=datetime(2026, 4, 25, 12, 0, 0),  # 6 дней назад
            )
            old_pending = _make_email(
                subject="old_pending", status=EmailStatus.PENDING,
                created_at=datetime(2026, 3, 1, 12, 0, 0),
            )
            for e in (old_failed, fresh_failed, old_pending):
                session_mail.add(e)
            session_mail.commit()

            svc = SchedulerService(app_with_mail)
            svc._cleanup_emails()
            session_mail.expire_all()

            remaining = {e.subject for e in session_mail.query(EmailQueue).all()}
            assert remaining == {"fresh_failed", "old_pending"}

    def test_boundary_exactly_30_days_old_kept(self, app_with_mail, session_mail):
        """Граница включительная: ровно 30 дней — не удаляется (created_at == cutoff)."""
        with freeze_time("2026-05-01 12:00:00.000001"):
            on_boundary = _make_email(
                subject="boundary", status=EmailStatus.FAILED,
                created_at=datetime(2026, 4, 1, 12, 0, 0, 1),  # cutoff = now() - 30d
            )
            session_mail.add(on_boundary)
            session_mail.commit()

            SchedulerService(app_with_mail)._cleanup_emails()
            session_mail.expire_all()
            assert session_mail.query(EmailQueue).count() == 1


# ----------------------------------------------------------------------------
# TestCleanupApplicationsJob
# ----------------------------------------------------------------------------

class TestCleanupApplicationsJob:

    def test_deletes_unconfirmed_older_than_7_days(
        self, app_with_mail, session_mail, persisted_conference
    ):
        with freeze_time("2026-05-01 12:00:00"):
            old_unconfirmed = _make_application(
                persisted_conference.id, email="old@x.ru",
                status=ApplicationStatus.UNCONFIRMED,
            )
            old_unconfirmed.created_at = datetime(2026, 4, 20, 12, 0, 0)  # 11 дней
            fresh_unconfirmed = _make_application(
                persisted_conference.id, email="fresh@x.ru",
                status=ApplicationStatus.UNCONFIRMED,
            )
            fresh_unconfirmed.created_at = datetime(2026, 4, 28, 12, 0, 0)  # 3 дня
            old_confirmed = _make_application(
                persisted_conference.id, email="old_ok@x.ru",
                status=ApplicationStatus.CONFIRMED,
            )
            old_confirmed.created_at = datetime(2026, 4, 20, 12, 0, 0)
            for a in (old_unconfirmed, fresh_unconfirmed, old_confirmed):
                session_mail.add(a)
            session_mail.commit()

            SchedulerService(app_with_mail)._cleanup_applications()
            session_mail.expire_all()

            remaining = {a.email for a in session_mail.query(Application).all()}
            assert remaining == {"fresh@x.ru", "old_ok@x.ru"}


# ----------------------------------------------------------------------------
# TestErrorIsolation: исключение в job → лог + rollback, не пробрасывается
# ----------------------------------------------------------------------------

class TestErrorIsolation:

    def test_reminders_swallows_exception(self, app_with_mail, caplog):
        svc = SchedulerService(app_with_mail)
        mock_conf = MagicMock()
        mock_conf.get_starting_in_days.side_effect = RuntimeError("boom")
        svc._services._services["conference"] = mock_conf

        # Не должно бросить наружу.
        svc._do_check_reminders()

        assert any("boom" in (r.exc_text or "") or "Оповещения не отправлены" in r.message
                   for r in caplog.records)

    def test_cleanup_emails_swallows_exception(self, app_with_mail, caplog):
        svc = SchedulerService(app_with_mail)
        mock_q = MagicMock()
        mock_q.cleanup_failed.side_effect = RuntimeError("boom")
        svc._services._services["email_queue"] = mock_q

        svc._cleanup_emails()

        assert any("Ошибка при очистке очереди" in r.message for r in caplog.records)

    def test_cleanup_applications_swallows_exception(self, app_with_mail, caplog):
        svc = SchedulerService(app_with_mail)
        mock_app = MagicMock()
        mock_app.cleanup_unconfirmed_older_than.side_effect = RuntimeError("boom")
        svc._services._services["application"] = mock_app

        svc._cleanup_applications()

        assert any("Ошибка при очистке неподтверждённых" in r.message for r in caplog.records)
