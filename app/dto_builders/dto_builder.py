from datetime import datetime

from app.dto.dto import ConferenceDTO, ApplicationDTO, ThesisDTO, ConferenceFileDTO, ScheduleItemDTO, ScheduleDTO
from app.exceptions.conversion_exception import EmptyRequiredFieldException, InvalidFieldFormatException
from app.models.application import GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum
from app.models.schedule_item import ScheduleItemType


def build_conference_dto(form):
    return ConferenceDTO (
        title=__parse_str(form.get("title"), "title"),
        description_md=__parse_str(form.get("description_md"), "description_md"),
        tagline=__parse_str(form.get("tagline"), "tagline", False),
        registration_deadline = __parse_date(form.get("registration_deadline"), "registration_deadline"),
        submission_deadline = __parse_date(form.get("submission_deadline"), "submission_deadline"),
        start_date = __parse_date(form.get("start_date"), "start_date"),
        end_date = __parse_date(form.get("end_date"), "end_date"),
        performance_time = __parse_int(form.get("performance_time"), "performance_time")
    )

def build_application_dto(form):
    is_worker, is_student = __parse_statuses(form)
    surname = __parse_str(form.get("surname"), "surname")
    name = __parse_str(form.get("name"), "name")
    patronymic = __parse_str(form.get("patronymic"), "patronymic", False)
    gender = __parse_enum(form.get("gender"), GenderEnum, "gender")
    birth_date = __parse_date(form.get("birth_date"), "birth_date")
    degree = __parse_enum(form.get("degree"), DegreeEnum, "degree")
    work_name = __parse_str(form.get("work_name"), "work_name", is_worker)
    work_place = __parse_str(form.get("work_place"), "work_place", is_worker)
    work_position = __parse_str(form.get("work_position"), "work_position", is_worker)
    study_name = __parse_str(form.get("study_name"), "study_name", is_student)
    study_place = __parse_str(form.get("study_place"), "study_place", is_student)
    study_level = __parse_enum(form.get("study_level"), EducationEnum, "study_level") if is_student else None

    participation_format = __parse_enum(form.get("participation_format"), ParticipationFormatEnum,
                                        "participation_format")
    email = __parse_str(form.get("email"), "email", True)

    if is_worker and not is_student:
        study_name = study_place = study_level = None
    if is_student and not is_worker:
        work_name = work_place = work_position = None

    return ApplicationDTO (
        surname=surname,
        name=name,
        patronymic=patronymic,
        gender=gender,
        birth_date=birth_date,
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
        email=email
    )

def build_thesis_dto(form):
    return ThesisDTO(
        authors=__parse_str(form.get("authors"), "authors"),
        title=__parse_str(form.get("title"), "title"),
        email=__parse_str(form.get("email"), "email")
    )

def build_file_dto(form):
    return ConferenceFileDTO(
        title=__parse_str(form.get("title"), "title")
    )

def __parse_date(value, field):
    if not value or not value.strip():
        raise EmptyRequiredFieldException(field)
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise InvalidFieldFormatException(field, "ожидается формат YYYY-MM-DD")

def __parse_time_string(value, field):
    if not value or not value.strip():
        raise EmptyRequiredFieldException(field)
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value.strip()
    except ValueError:
        raise InvalidFieldFormatException(field, "ожидается формат ISO datetime (YYYY-MM-DDTHH:MM:SS)")

def __parse_int(value, field):
    if value is None:
        raise EmptyRequiredFieldException(field)
    if isinstance(value, int):
        result = value
    else:
        if not value or not value.strip():
            raise EmptyRequiredFieldException(field)
        try:
            result = int(value.strip())
        except ValueError:
            raise InvalidFieldFormatException(field, "должно быть числом")
    if result <= 0:
        raise InvalidFieldFormatException(field, "должно быть положительным числом")
    return result

def __parse_str(value, field, required = True):
    if value is None:
        value = ""
    value = value.strip()
    if required and not value:
        raise EmptyRequiredFieldException(field)
    return value if value else None

def __parse_enum(value, enum_class, field):
    if not value or not value.strip():
        raise EmptyRequiredFieldException(field)
    try:
         return enum_class(value.strip())
    except:
        raise InvalidFieldFormatException(field, f"недопустимое значение {value}")

def __parse_statuses(form):
    statuses = form.getlist("status")
    if statuses is None:
        raise EmptyRequiredFieldException("status")
    if not isinstance(statuses, list):
        raise InvalidFieldFormatException("status", "Ожидается список статусов")

    is_worker = "worker" in statuses
    is_student = "student" in statuses

    return is_worker, is_student


def __build_schedule_item_dto(data: dict) -> ScheduleItemDTO:
    item_type = __parse_enum(data.get("item_type"), ScheduleItemType, "item_type")
    global_order = __parse_int(data.get("global_order"), "global_order")

    dto = ScheduleItemDTO(
        item_type=item_type,
        global_order=global_order
    )

    if item_type == ScheduleItemType.DAY:
        dto.day_date = __parse_date(data.get("day_date"), "day_date")
        dto.day_title = __parse_str(data.get("day_title"), "day_title", True)
        dto.day_start_time = __parse_str(data.get("day_start_time"), "day_start_time", True)

    elif item_type == ScheduleItemType.TALK:
        dto.application_id = __parse_int(data.get("application_id"), "application_id")
        dto.talk_speaker = __parse_str(data.get("talk_speaker"), "talk_speaker", True)
        dto.talk_title = __parse_str(data.get("talk_title"), "talk_title", True)
        dto.talk_duration = __parse_int(data.get("talk_duration"), "talk_duration")
        dto.start_time = __parse_time_string(data.get("start_time"), "start_time")
        dto.end_time = __parse_time_string(data.get("end_time"), "end_time")

    elif item_type == ScheduleItemType.BREAK:
        dto.break_title = __parse_str(data.get("break_title"), "break_title", True)
        dto.break_duration = __parse_int(data.get("break_duration"), "break_duration")
        dto.start_time = __parse_time_string(data.get("start_time"), "start_time")
        dto.end_time = __parse_time_string(data.get("end_time"), "end_time")

    elif item_type == ScheduleItemType.TEXT:
        dto.text_content = __parse_str(data.get("text_content"), "text_content", True)

    return dto


def build_schedule_dto(data: dict) -> ScheduleDTO:
    schedule_data = data.get("schedule")
    if not schedule_data or not isinstance(schedule_data, list):
        raise InvalidFieldFormatException("schedule", "должен быть списком")

    schedule_dtos = []
    for item_data in schedule_data:
        item_dto = __build_schedule_item_dto(item_data)
        schedule_dtos.append(item_dto)

    return ScheduleDTO(
        schedule=schedule_dtos
    )