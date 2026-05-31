from datetime import date

import pytest

from app.dto.dto import (
    ConferenceDTO, ApplicationDTO, ThesisDTO, ConferenceFileDTO,
    ScheduleDTO, )
from app.dto_builders.dto_builder import (
    build_conference_dto,
    build_application_dto,
    build_thesis_dto,
    build_file_dto,
    build_schedule_dto,
)
from app.exceptions.conversion_exception import EmptyRequiredFieldException, InvalidFieldFormatException
from app.models.application import GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum
from app.models.schedule_item import ScheduleItemType
from tests.factories import (
    MockForm, make_conference_form, make_application_form,
    make_thesis_form, make_file_form, _day_item_data, _talk_item_data, _break_item_data, _text_item_data,
)

class TestBuildConferenceDTO:

    def test_valid_full_form(self):
        form = make_conference_form(tagline="Cool tagline")
        dto = build_conference_dto(form)
        assert isinstance(dto, ConferenceDTO)
        assert dto.title == "Conf Title"
        assert dto.description_md == "# Desc"
        assert dto.tagline == "Cool tagline"
        assert dto.registration_deadline == date(2025, 6, 1)
        assert dto.submission_deadline == date(2025, 7, 1)
        assert dto.start_date == date(2025, 8, 1)
        assert dto.end_date == date(2025, 8, 3)
        assert dto.performance_time == 15

    def test_optional_tagline_empty(self):
        form = make_conference_form(tagline="   ")
        dto = build_conference_dto(form)
        assert dto.tagline is None

    def test_optional_tagline_missing(self):
        form = make_conference_form()
        form.pop("tagline", None)
        dto = build_conference_dto(form)
        assert dto.tagline is None

    def test_missing_required_title(self):
        form = make_conference_form()
        form.pop("title")
        with pytest.raises(EmptyRequiredFieldException):
            build_conference_dto(form)

    def test_empty_required_title(self):
        form = make_conference_form(title="   ")
        with pytest.raises(EmptyRequiredFieldException):
            build_conference_dto(form)

    def test_missing_required_description(self):
        form = make_conference_form()
        form.pop("description_md")
        with pytest.raises(EmptyRequiredFieldException):
            build_conference_dto(form)

    def test_invalid_date_format(self):
        form = make_conference_form(start_date="01-08-2025")
        with pytest.raises(InvalidFieldFormatException):
            build_conference_dto(form)

    def test_missing_date(self):
        form = make_conference_form()
        form.pop("start_date")
        with pytest.raises(EmptyRequiredFieldException):
            build_conference_dto(form)

    def test_empty_date(self):
        form = make_conference_form(start_date="   ")
        with pytest.raises(EmptyRequiredFieldException):
            build_conference_dto(form)

    def test_performance_time_as_int(self):
        form = make_conference_form(performance_time=20)
        dto = build_conference_dto(form)
        assert dto.performance_time == 20

    def test_performance_time_zero(self):
        form = make_conference_form(performance_time=0)
        with pytest.raises(InvalidFieldFormatException):
            build_conference_dto(form)

    def test_performance_time_negative(self):
        form = make_conference_form(performance_time=-5)
        with pytest.raises(InvalidFieldFormatException):
            build_conference_dto(form)

    def test_performance_time_not_a_number(self):
        form = make_conference_form(performance_time="abc")
        with pytest.raises(InvalidFieldFormatException):
            build_conference_dto(form)

    def test_performance_time_none(self):
        form = make_conference_form()
        form["performance_time"] = None
        with pytest.raises(EmptyRequiredFieldException):
            build_conference_dto(form)

    def test_whitespace_trimmed(self):
        form = make_conference_form(title="  Spaced Title  ")
        dto = build_conference_dto(form)
        assert dto.title == "Spaced Title"

class TestBuildApplicationDTO:

    def test_worker_and_student(self):
        form = make_application_form()
        dto = build_application_dto(form)
        assert isinstance(dto, ApplicationDTO)
        assert dto.is_worker is True
        assert dto.is_student is True
        assert dto.work_name == "Test Corp"
        assert dto.study_name == "Test Uni"
        assert dto.study_level == EducationEnum.MASTER

    def test_worker_only(self):
        form = make_application_form(_lists={"status": ["worker"]})
        dto = build_application_dto(form)
        assert dto.is_worker is True
        assert dto.is_student is False
        assert dto.work_name == "Test Corp"
        assert dto.study_name is None
        assert dto.study_place is None
        assert dto.study_level is None

    def test_student_only(self):
        form = make_application_form(_lists={"status": ["student"]})
        dto = build_application_dto(form)
        assert dto.is_worker is False
        assert dto.is_student is True
        assert dto.study_name == "Test Uni"
        assert dto.work_name is None
        assert dto.work_place is None
        assert dto.work_position is None

    def test_missing_status(self):
        form = make_application_form(_lists={"status": None})
        with pytest.raises(EmptyRequiredFieldException):
            build_application_dto(form)

    def test_status_not_a_list(self):
        form = make_application_form(_lists={"status": "worker"})
        with pytest.raises(InvalidFieldFormatException):
            build_application_dto(form)

    def test_missing_required_surname(self):
        form = make_application_form()
        form.pop("surname")
        with pytest.raises(EmptyRequiredFieldException):
            build_application_dto(form)

    def test_optional_patronymic_empty(self):
        form = make_application_form(patronymic="   ")
        dto = build_application_dto(form)
        assert dto.patronymic is None

    def test_invalid_gender(self):
        form = make_application_form(gender="unknown")
        with pytest.raises(InvalidFieldFormatException):
            build_application_dto(form)

    def test_invalid_degree(self):
        form = make_application_form(degree="phd")
        with pytest.raises(InvalidFieldFormatException):
            build_application_dto(form)

    def test_invalid_participation_format(self):
        form = make_application_form(participation_format="hybrid")
        with pytest.raises(InvalidFieldFormatException):
            build_application_dto(form)

    def test_invalid_birth_date(self):
        form = make_application_form(birth_date="15-01-2000")
        with pytest.raises(InvalidFieldFormatException):
            build_application_dto(form)

    def test_missing_email(self):
        form = make_application_form()
        form.pop("email")
        with pytest.raises(EmptyRequiredFieldException):
            build_application_dto(form)

    def test_worker_fields_required_when_worker(self):
        form = make_application_form(_lists={"status": ["worker"]}, work_name="   ")
        with pytest.raises(EmptyRequiredFieldException):
            build_application_dto(form)

    def test_student_fields_required_when_student(self):
        form = make_application_form(_lists={"status": ["student"]}, study_name="   ")
        with pytest.raises(EmptyRequiredFieldException):
            build_application_dto(form)

    def test_enum_values_parsed_correctly(self):
        form = make_application_form(gender="female", degree="candidate", participation_format="online")
        dto = build_application_dto(form)
        assert dto.gender == GenderEnum.FEMALE
        assert dto.degree == DegreeEnum.CANDIDATE
        assert dto.participation_format == ParticipationFormatEnum.ONLINE

class TestBuildThesisDTO:

    def test_valid_form(self):
        dto = build_thesis_dto(make_thesis_form())
        assert isinstance(dto, ThesisDTO)
        assert dto.authors == "Ivanov I.I."
        assert dto.title == "Test Thesis"
        assert dto.email == "ivan@test.com"

    def test_missing_authors(self):
        form = make_thesis_form()
        form.pop("authors")
        with pytest.raises(EmptyRequiredFieldException):
            build_thesis_dto(form)

    def test_missing_title(self):
        form = make_thesis_form()
        form.pop("title")
        with pytest.raises(EmptyRequiredFieldException):
            build_thesis_dto(form)

    def test_missing_email(self):
        form = make_thesis_form()
        form.pop("email")
        with pytest.raises(EmptyRequiredFieldException):
            build_thesis_dto(form)

    def test_empty_authors(self):
        with pytest.raises(EmptyRequiredFieldException):
            build_thesis_dto(make_thesis_form(authors="   "))

    def test_whitespace_trimmed(self):
        dto = build_thesis_dto(make_thesis_form(authors="  Ivanov I.I.  "))
        assert dto.authors == "Ivanov I.I."

class TestBuildFileDTO:

    def test_valid_form(self):
        dto = build_file_dto(make_file_form())
        assert isinstance(dto, ConferenceFileDTO)
        assert dto.title == "Proceedings 2024"

    def test_missing_title(self):
        with pytest.raises(EmptyRequiredFieldException):
            build_file_dto(MockForm({}))

    def test_empty_title(self):
        with pytest.raises(EmptyRequiredFieldException):
            build_file_dto(make_file_form(title="   "))

    def test_whitespace_trimmed(self):
        dto = build_file_dto(make_file_form(title="  My File  "))
        assert dto.title == "My File"

class TestBuildScheduleDTO:

    def test_valid_day_item(self):
        dto = build_schedule_dto({"schedule": [_day_item_data()]})
        assert isinstance(dto, ScheduleDTO)
        assert len(dto.schedule) == 1
        item = dto.schedule[0]
        assert item.item_type == ScheduleItemType.DAY
        assert item.global_order == 1
        assert item.day_date == date(2025, 8, 1)
        assert item.day_title == "Day 1"
        assert item.day_start_time == "09:00"

    def test_valid_talk_item(self):
        dto = build_schedule_dto({"schedule": [_talk_item_data()]})
        item = dto.schedule[0]
        assert item.item_type == ScheduleItemType.TALK
        assert item.application_id == 1
        assert item.talk_speaker == "Ivanov I.I."
        assert item.talk_title == "My Talk"
        assert item.talk_duration == 15
        assert item.start_time == "2025-08-01T09:00:00"
        assert item.end_time == "2025-08-01T09:15:00"

    def test_valid_break_item(self):
        dto = build_schedule_dto({"schedule": [_break_item_data()]})
        item = dto.schedule[0]
        assert item.item_type == ScheduleItemType.BREAK
        assert item.break_title == "Coffee"
        assert item.break_duration == 15

    def test_valid_text_item(self):
        dto = build_schedule_dto({"schedule": [_text_item_data()]})
        item = dto.schedule[0]
        assert item.item_type == ScheduleItemType.TEXT
        assert item.text_content == "Welcome!"

    def test_multiple_items(self):
        dto = build_schedule_dto({"schedule": [
            _day_item_data(),
            _talk_item_data(),
            _break_item_data(),
            _text_item_data(),
        ]})
        assert len(dto.schedule) == 4
        assert dto.schedule[0].item_type == ScheduleItemType.DAY
        assert dto.schedule[1].item_type == ScheduleItemType.TALK
        assert dto.schedule[2].item_type == ScheduleItemType.BREAK
        assert dto.schedule[3].item_type == ScheduleItemType.TEXT

    def test_missing_schedule_key(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({})

    def test_schedule_not_a_list(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": "not a list"})

    def test_empty_schedule_list(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": []})

    def test_invalid_item_type(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": [_day_item_data(item_type="invalid")]})

    def test_missing_item_type(self):
        item = _day_item_data()
        item.pop("item_type")
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [item]})

    def test_missing_global_order(self):
        item = _day_item_data()
        item.pop("global_order")
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [item]})

    def test_talk_missing_required_field(self):
        item = _talk_item_data()
        item.pop("talk_speaker")
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [item]})

    def test_break_missing_required_field(self):
        item = _break_item_data()
        item.pop("break_title")
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [item]})

    def test_text_missing_required_field(self):
        item = _text_item_data()
        item.pop("text_content")
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [item]})

    def test_day_invalid_date(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": [_day_item_data(day_date="01-08-2025")]})

    def test_talk_invalid_time(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": [_talk_item_data(start_time="not-a-time")]})

    def test_talk_zero_duration(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": [_talk_item_data(talk_duration=0)]})

    def test_negative_global_order(self):
        with pytest.raises(InvalidFieldFormatException):
            build_schedule_dto({"schedule": [_day_item_data(global_order=-1)]})

    def test_talk_empty_start_time(self):
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [_talk_item_data(start_time="   ")]})

    def test_talk_empty_string_duration(self):
        with pytest.raises(EmptyRequiredFieldException):
            build_schedule_dto({"schedule": [_talk_item_data(talk_duration="   ")]})

    def test_time_string_with_z_suffix(self):
        item = _talk_item_data(start_time="2025-08-01T09:00:00Z", end_time="2025-08-01T09:15:00Z")
        dto = build_schedule_dto({"schedule": [item]})
        assert dto.schedule[0].start_time == "2025-08-01T09:00:00Z"
