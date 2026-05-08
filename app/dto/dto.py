from dataclasses import dataclass
from datetime import date
from typing import Any

from app.models.application import GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum
from app.models.schedule_item import ScheduleItemType


@dataclass
class ThesisInApplicationDTO:
    """Данные тезиса в составе заявки (для API-ответа)."""

    id: int
    authors: str
    title: str
    file_name: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'authors': self.authors,
            'title': self.title,
            'file_name': self.file_name,
            'status': self.status
        }


@dataclass
class ThesisDTO:
    """Данные для подачи тезисов участником."""

    authors: str
    title: str
    email: str


@dataclass
class ThesisScheduleDTO:
    """Данные тезиса для редактора расписания."""

    id: int
    speaker_name: str
    title: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "speaker_name": self.speaker_name,
            "title": self.title
        }


@dataclass
class ConferenceDTO:
    """Данные для создания или редактирования конференции."""

    title: str
    description_md: str
    tagline: str
    registration_deadline: date
    submission_deadline: date
    start_date: date
    end_date: date
    performance_time: int


@dataclass
class ConferenceScheduleDTO:
    """Краткие данные конференции для редактора расписания."""

    id: int
    title: str
    start_date: date
    end_date: date
    performance_time: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "performance_time": self.performance_time
        }


@dataclass
class FullApplicationDTO:
    """Полные данные заявки для API-ответа. Содержит вычисляемые свойства full_name и age."""

    id: int
    surname: str
    name: str
    patronymic: str | None

    gender: str
    birth_date: date

    degree: str

    is_worker: bool
    is_student: bool

    work_name: str | None
    work_place: str | None
    work_position: str | None

    study_name: str | None
    study_place: str | None
    study_level: str | None

    participation_format: str
    email: str

    theses: list[ThesisInApplicationDTO]

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'full_name': self.full_name,
            'gender': self.gender,
            'birth_date': self.birth_date.isoformat(),
            'age': self.age,
            'degree': self.degree,
            'is_worker': self.is_worker,
            'is_student': self.is_student,
            'work_name': self.work_name,
            'work_place': self.work_place,
            'work_position': self.work_position,
            'study_name': self.study_name,
            'study_place': self.study_place,
            'study_level': self.study_level,
            'participation_format': self.participation_format,
            'email': self.email,
            'theses': [t.to_dict() for t in self.theses]
        }

    @property
    def full_name(self) -> str:
        parts = [self.surname, self.name]
        if self.patronymic:
            parts.append(self.patronymic)
        return " ".join(parts)

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )


@dataclass
class ApplicationDTO:
    """Данные заявки участника, разобранные из формы регистрации."""

    surname: str
    name: str
    patronymic: str | None

    gender: GenderEnum
    birth_date: date

    degree: DegreeEnum

    is_worker: bool
    is_student: bool

    work_name: str | None
    work_place: str | None
    work_position: str | None

    study_name: str | None
    study_place: str | None
    study_level: EducationEnum | None

    participation_format: ParticipationFormatEnum
    email: str


@dataclass
class FullScheduleDTO:
    """Полные данные расписания конференции для редактора."""

    conference: ConferenceScheduleDTO
    applications: list[ThesisScheduleDTO]
    schedule: list[dict]

    def to_dict(self) -> dict[str, Any]:
        return {
            "conference": self.conference.to_dict(),
            "applications": [app.to_dict() for app in self.applications],
            "schedule": self.schedule
        }


@dataclass
class ConferenceFileDTO:
    """Данные файла конференции из формы загрузки."""

    title: str


@dataclass
class ScheduleItemDTO:
    """Элемент расписания. Заполненные поля зависят от значения item_type."""

    item_type: ScheduleItemType
    global_order: int

    day_date: date | None = None
    day_title: str | None = None
    day_start_time: str | None = None

    application_id: int | None = None
    talk_speaker: str | None = None
    talk_title: str | None = None
    talk_duration: int | None = None
    start_time: str | None = None
    end_time: str | None = None

    break_title: str | None = None
    break_duration: int | None = None

    text_content: str | None = None


@dataclass
class ScheduleDTO:
    """Список элементов расписания из запроса на сохранение."""

    schedule: list[ScheduleItemDTO]
