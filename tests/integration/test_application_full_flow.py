from datetime import date, timedelta
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from app.dto.dto import ApplicationDTO, ConferenceDTO, ThesisDTO
from app.models.application import (
    ApplicationStatus, GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum,
)
from app.models.email_queue import EmailQueue, EmailStatus, QueueType
from app.models.thesis import ThesisStatus


# Минимальный валидный PDF — магические байты "%PDF-" в начале распознаются
# библиотекой filetype как pdf.
PDF_MAGIC = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 1024


@pytest.fixture
def pdf_file():
    """FileStorage с валидной PDF-сигнатурой."""
    return FileStorage(
        stream=BytesIO(PDF_MAGIC),
        filename="thesis.pdf",
        content_type="application/pdf",
    )


@pytest.fixture
def session_mail(app_with_mail):
    """Свежая сессия для app_with_mail."""
    from app.core import database
    s = database.Session()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


def _make_conf_dto(title="Конференция-2026"):
    today = date.today()
    return ConferenceDTO(
        title=title,
        description_md="# Описание",
        tagline="Тематика",
        registration_deadline=today + timedelta(days=30),
        submission_deadline=today + timedelta(days=45),
        start_date=today + timedelta(days=60),
        end_date=today + timedelta(days=62),
        performance_time=15,
    )


def _make_app_dto(email="participant@test.com"):
    return ApplicationDTO(
        surname="Иванов",
        name="Иван",
        patronymic="Иванович",
        email=email,
        gender=GenderEnum.MALE,
        birth_date=date(2000, 1, 1),
        degree=DegreeEnum.NONE,
        is_worker=False,
        is_student=True,
        work_name=None, work_place=None, work_position=None,
        study_name="UrFU",
        study_place="Екатеринбург",
        study_level=EducationEnum.MASTER,
        participation_format=ParticipationFormatEnum.OFFLINE,
    )


class TestFullApplicationFlow:
    """Сквозной сценарий приёма заявки и работы с тезисом."""

    def test_admin_creates_conference_then_participant_submits_application(
        self, app_with_mail, session_mail
    ):
        services = app_with_mail.extensions["services"]

        # Шаг 1. Админ создаёт конференцию.
        conference = services.conference.create_conference(_make_conf_dto(), session_mail)
        session_mail.commit()
        assert conference.id is not None
        assert conference.description_html  # html сгенерирован из md

        # Шаг 2. Участник подаёт заявку.
        app_obj = services.application.create_application(
            conference.id, _make_app_dto(), session_mail
        )
        session_mail.commit()
        assert app_obj.id is not None
        assert app_obj.status == ApplicationStatus.CONFIRMED
        assert app_obj.conference_id == conference.id

    def test_participant_uploads_thesis_after_confirmed_application(
        self, app_with_mail, session_mail, pdf_file
    ):
        services = app_with_mail.extensions["services"]
        conference = services.conference.create_conference(_make_conf_dto(), session_mail)
        session_mail.commit()
        services.application.create_application(
            conference.id, _make_app_dto(), session_mail
        )
        session_mail.commit()

        # Загрузка тезиса
        thesis = services.thesis.create_thesis(
            conference.id, pdf_file,
            ThesisDTO(authors="И. Иванов", title="Test", email="participant@test.com"),
            session_mail,
        )
        session_mail.commit()
        assert thesis.id is not None
        assert thesis.status == ThesisStatus.PENDING
        expected_prefix = os.path.join(str(conference.id), "theses") + os.sep
        assert thesis.file_path.startswith(expected_prefix)

    def test_admin_accepts_thesis_and_email_queued(self, app_with_mail, session_mail, pdf_file):
        """Смена статуса тезиса должна приводить к постановке письма в очередь."""
        services = app_with_mail.extensions["services"]

        # Готовим состояние: конференция + заявка + тезис
        conference = services.conference.create_conference(_make_conf_dto(), session_mail)
        session_mail.commit()
        services.application.create_application(
            conference.id, _make_app_dto(), session_mail
        )
        session_mail.commit()
        thesis = services.thesis.create_thesis(
            conference.id, pdf_file,
            ThesisDTO(authors="И. Иванов", title="Test", email="participant@test.com"),
            session_mail,
        )
        session_mail.commit()

        # Меняем статус и ставим письмо в очередь через NotificationService.
        # render_template требует Flask app_context.
        services.thesis.update_thesis_status(thesis.id, "accepted", session_mail)
        with app_with_mail.app_context():
            services.notification.send_thesis_status(thesis, session_mail)
        session_mail.commit()

        # В очереди — одно индивидуальное письмо адресату заявки.
        queued = session_mail.query(EmailQueue).all()
        assert len(queued) == 1
        msg = queued[0]
        assert msg.recipient == "participant@test.com"
        assert msg.queue_type == QueueType.INDIVIDUAL
        assert msg.status == EmailStatus.PENDING
        assert "приняты" in msg.subject.lower() or "приняты" in msg.html_body.lower()

    def test_admin_publishes_schedule_and_mass_email_queued(
        self, app_with_mail, session_mail
    ):
        services = app_with_mail.extensions["services"]
        conference = services.conference.create_conference(_make_conf_dto(), session_mail)
        session_mail.commit()
        services.application.create_application(
            conference.id, _make_app_dto(email="p1@test.com"), session_mail
        )
        services.application.create_application(
            conference.id, _make_app_dto(email="p2@test.com"), session_mail
        )
        session_mail.commit()

        applications = services.application.get_all_applications(session_mail)
        with app_with_mail.app_context():
            services.notification.send_schedule_published(
                applications, conference, session_mail
            )
        session_mail.commit()

        mass = session_mail.query(EmailQueue).filter_by(queue_type=QueueType.MASS).all()
        recipients = sorted(m.recipient for m in mass)
        assert recipients == ["p1@test.com", "p2@test.com"]

    def test_duplicate_application_blocked(self, app_with_mail, session_mail):
        from app.exceptions.conflict_exception import ApplicationAlreadyExists
        services = app_with_mail.extensions["services"]
        conference = services.conference.create_conference(_make_conf_dto(), session_mail)
        session_mail.commit()
        services.application.create_application(
            conference.id, _make_app_dto(), session_mail
        )
        session_mail.commit()

        with pytest.raises(ApplicationAlreadyExists):
            services.application.create_application(
                conference.id, _make_app_dto(), session_mail
            )

    def test_get_full_applications_returns_dto_with_theses(
        self, app_with_mail, session_mail, pdf_file
    ):
        services = app_with_mail.extensions["services"]
        conference = services.conference.create_conference(_make_conf_dto(), session_mail)
        session_mail.commit()
        services.application.create_application(
            conference.id, _make_app_dto(), session_mail
        )
        session_mail.commit()
        services.thesis.create_thesis(
            conference.id, pdf_file,
            ThesisDTO(authors="И. Иванов", title="Test", email="participant@test.com"),
            session_mail,
        )
        session_mail.commit()

        full = services.application.get_full_applications_for_conference(
            conference.id, session_mail
        )
        assert len(full) == 1
        # маппер вернул объект с заявкой+тезисами
        result = full[0]
        assert getattr(result, "email", None) == "participant@test.com"
