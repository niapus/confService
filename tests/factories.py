from datetime import date, timedelta, datetime


def make_conference(
    conf_id=1,
    title="Test Conference",
    description_md="# Hello",
    description_html="<h1>Hello</h1>",
    tagline="Test tagline",
    registration_deadline=None,
    submission_deadline=None,
    start_date=None,
    end_date=None,
    performance_time=15,
):
    from app.models.conference import Conference
    today = date.today()
    conf = Conference()
    conf.id = conf_id
    conf.title = title
    conf.description_md = description_md
    conf.description_html = description_html
    conf.tagline = tagline
    conf.registration_deadline = registration_deadline or (today + timedelta(days=30))
    conf.submission_deadline = submission_deadline or (today + timedelta(days=45))
    conf.start_date = start_date or (today + timedelta(days=60))
    conf.end_date = end_date or (today + timedelta(days=62))
    conf.performance_time = performance_time
    conf.applications = []
    conf.files = []
    conf.schedule_items = []
    return conf


def make_application(
    app_id=1,
    conf_id=1,
    surname="Ivanov",
    name="Ivan",
    patronymic="Ivanovich",
    email="ivan@test.com",
    status=None,
    gender=None,
    birth_date=None,
    degree=None,
    is_worker=False,
    is_student=True,
    work_name=None,
    work_place=None,
    work_position=None,
    study_name="Test University",
    study_place="Test City",
    study_level=None,
    participation_format=None,
    created_at=None,
):
    from app.models.application import (
        Application, ApplicationStatus, GenderEnum, DegreeEnum,
        EducationEnum, ParticipationFormatEnum
    )
    if status is None:
        status = ApplicationStatus.CONFIRMED
    if gender is None:
        gender = GenderEnum.MALE
    if degree is None:
        degree = DegreeEnum.NONE
    if study_level is None:
        study_level = EducationEnum.MASTER
    if participation_format is None:
        participation_format = ParticipationFormatEnum.OFFLINE
    app_obj = Application()
    app_obj.id = app_id
    app_obj.conference_id = conf_id
    app_obj.surname = surname
    app_obj.name = name
    app_obj.patronymic = patronymic
    app_obj.email = email
    app_obj.status = status
    app_obj.gender = gender
    app_obj.birth_date = birth_date or date(2000, 1, 1)
    app_obj.degree = degree
    app_obj.is_worker = is_worker
    app_obj.is_student = is_student
    app_obj.work_name = work_name
    app_obj.work_place = work_place
    app_obj.work_position = work_position
    app_obj.study_name = study_name
    app_obj.study_place = study_place
    app_obj.study_level = study_level
    app_obj.participation_format = participation_format
    app_obj.created_at = created_at or datetime.now()
    app_obj.theses = []
    return app_obj


def make_application_dto(
    surname="Ivanov",
    name="Ivan",
    patronymic="Ivanovich",
    email="ivan@test.com",
    gender=None,
    birth_date=None,
    degree=None,
    is_worker=False,
    is_student=True,
    work_name=None,
    work_place=None,
    work_position=None,
    study_name="Test University",
    study_place="Test City",
    study_level=None,
    participation_format=None,
):
    from app.models.application import GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum
    from app.dto.dto import ApplicationDTO
    if gender is None:
        gender = GenderEnum.MALE
    if degree is None:
        degree = DegreeEnum.NONE
    if study_level is None:
        study_level = EducationEnum.MASTER
    if participation_format is None:
        participation_format = ParticipationFormatEnum.OFFLINE
    return ApplicationDTO(
        surname=surname,
        name=name,
        patronymic=patronymic,
        email=email,
        gender=gender,
        birth_date=birth_date or date(2000, 1, 1),
        degree=degree,
        is_worker=is_worker,
        is_student=is_student,
        work_name=work_name,
        work_place=work_place,
        work_position=work_position,
        study_name=study_name,
        study_place=study_place,
        study_level=study_level,
        participation_format=participation_format,
    )


def make_conference_dto(
    title="New Conference",
    description_md="# Desc",
    tagline="Tagline",
    registration_deadline=None,
    submission_deadline=None,
    start_date=None,
    end_date=None,
    performance_time=15,
):
    from app.dto.dto import ConferenceDTO
    today = date.today()
    return ConferenceDTO(
        title=title,
        description_md=description_md,
        tagline=tagline,
        registration_deadline=registration_deadline or (today + timedelta(days=30)),
        submission_deadline=submission_deadline or (today + timedelta(days=45)),
        start_date=start_date or (today + timedelta(days=60)),
        end_date=end_date or (today + timedelta(days=62)),
        performance_time=performance_time,
    )


def make_thesis(
    thesis_id=1,
    application_id=1,
    authors="Ivanov I.I.",
    title="Test Thesis",
    file_path="1/theses/test.pdf",
    file_name="test.pdf",
    status=None,
):
    from app.models.thesis import Thesis, ThesisStatus
    if status is None:
        status = ThesisStatus.PENDING
    thesis = Thesis()
    thesis.id = thesis_id
    thesis.application_id = application_id
    thesis.authors = authors
    thesis.title = title
    thesis.file_path = file_path
    thesis.file_name = file_name
    thesis.status = status
    return thesis


def make_thesis_dto(authors="Ivanov I.I.", title="Test Thesis", email="ivan@test.com"):
    from app.dto.dto import ThesisDTO
    return ThesisDTO(authors=authors, title=title, email=email)


def make_email_queue(
    eq_id=1,
    subject="Test Subject",
    recipient="test@test.com",
    html_body="<p>Test</p>",
    queue_type=None,
    status=None,
    attempts=0,
):
    from app.models.email_queue import EmailQueue, EmailStatus, QueueType
    if queue_type is None:
        queue_type = QueueType.INDIVIDUAL
    if status is None:
        status = EmailStatus.PENDING
    eq = EmailQueue()
    eq.id = eq_id
    eq.subject = subject
    eq.recipient = recipient
    eq.html_body = html_body
    eq.queue_type = queue_type
    eq.status = status
    eq.attempts = attempts
    return eq


def make_conference_file(
    file_id=1,
    conf_id=1,
    file_type=None,
    original_name="test.pdf",
    file_path="1/proceedings/test.pdf",
    title="Proceedings",
):
    from app.models.conference_file import ConferenceFile, ConferenceFileType
    if file_type is None:
        file_type = ConferenceFileType.PROCEEDINGS
    cf = ConferenceFile()
    cf.id = file_id
    cf.conference_id = conf_id
    cf.file_type = file_type
    cf.original_name = original_name
    cf.file_path = file_path
    cf.title = title
    return cf


def make_schedule_item(
    item_id=1,
    conf_id=1,
    item_type=None,
    global_order=1,
    day_date=None,
    day_title="Day 1",
    day_start_time="09:00",
):
    from app.models.schedule_item import ScheduleItem, ScheduleItemType
    if item_type is None:
        item_type = ScheduleItemType.DAY
    si = ScheduleItem()
    si.id = item_id
    si.conference_id = conf_id
    si.item_type = item_type
    si.global_order = global_order
    si.day_date = day_date or date.today()
    si.day_title = day_title
    si.day_start_time = day_start_time
    return si


def make_schedule_dto():
    from app.dto.dto import ScheduleDTO, ScheduleItemDTO
    from app.models.schedule_item import ScheduleItemType
    return ScheduleDTO(schedule=[
        ScheduleItemDTO(
            item_type=ScheduleItemType.DAY,
            global_order=1,
            day_date=date.today(),
            day_title="Day 1",
            day_start_time="09:00",
        ),
        ScheduleItemDTO(
            item_type=ScheduleItemType.TALK,
            global_order=2,
            application_id=1,
            talk_speaker="Ivanov I.I.",
            talk_title="Test Talk",
            talk_duration=15,
            start_time="09:00",
            end_time="09:15",
        ),
    ])


# ---------------------------------------------------------------------------
# Form mocks & factories for dto_builder tests
# ---------------------------------------------------------------------------

class MockForm(dict):
    """Dict-like form mock that also supports getlist()."""

    def __init__(self, data=None, lists=None):
        super().__init__(data or {})
        self._lists = lists or {}

    def getlist(self, key):
        return self._lists.get(key)


def make_conference_form(**overrides):
    data = {
        "title": "Conf Title",
        "description_md": "# Desc",
        "tagline": "Cool tagline",
        "registration_deadline": "2025-06-01",
        "submission_deadline": "2025-07-01",
        "start_date": "2025-08-01",
        "end_date": "2025-08-03",
        "performance_time": "15",
    }
    data.update(overrides)
    return MockForm(data)


def make_application_form(**overrides):
    lists = overrides.pop("_lists", {"status": ["worker", "student"]})
    data = {
        "surname": "Ivanov",
        "name": "Ivan",
        "patronymic": "Ivanovich",
        "gender": "male",
        "birth_date": "2000-01-15",
        "degree": "none",
        "work_name": "Test Corp",
        "work_place": "Moscow",
        "work_position": "Engineer",
        "study_name": "Test Uni",
        "study_place": "Test City",
        "study_level": "education_mag",
        "participation_format": "offline",
        "email": "ivan@test.com",
    }
    data.update(overrides)
    return MockForm(data, lists=lists)


def make_thesis_form(**overrides):
    data = {"authors": "Ivanov I.I.", "title": "Test Thesis", "email": "ivan@test.com"}
    data.update(overrides)
    return MockForm(data)


def make_file_form(**overrides):
    data = {"title": "Proceedings 2024"}
    data.update(overrides)
    return MockForm(data)


def make_schedule_form_data(**overrides):
    data = {"schedule": [
        _day_item_data(),
        _talk_item_data(),
    ]}
    data.update(overrides)
    return data


def _day_item_data(**overrides):
    item = {
        "item_type": "day",
        "global_order": 1,
        "day_date": "2025-08-01",
        "day_title": "Day 1",
        "day_start_time": "09:00",
    }
    item.update(overrides)
    return item


def _talk_item_data(**overrides):
    item = {
        "item_type": "talk",
        "global_order": 2,
        "application_id": 1,
        "talk_speaker": "Ivanov I.I.",
        "talk_title": "My Talk",
        "talk_duration": 15,
        "start_time": "2025-08-01T09:00:00",
        "end_time": "2025-08-01T09:15:00",
    }
    item.update(overrides)
    return item


def _break_item_data(**overrides):
    item = {
        "item_type": "break",
        "global_order": 3,
        "break_title": "Coffee",
        "break_duration": 15,
        "start_time": "2025-08-01T09:15:00",
        "end_time": "2025-08-01T09:30:00",
    }
    item.update(overrides)
    return item


def _text_item_data(**overrides):
    item = {
        "item_type": "text",
        "global_order": 4,
        "text_content": "Welcome!",
    }
    item.update(overrides)
    return item
