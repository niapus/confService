from dataclasses import dataclass
from datetime import date
from typing import Optional, List

from app.models.application import GenderEnum, DegreeEnum, EducationEnum, ParticipationFormatEnum
from app.models.schedule_item import ScheduleItemType


@dataclass
class ThesisInApplicationDTO:
    id: int
    authors: str
    title: str
    file_name: str
    status: str

    def to_dict(self):
        return {
            'id': self.id,
            'authors': self.authors,
            'title': self.title,
            'file_name': self.file_name,
            'status': self.status
        }

@dataclass
class ThesisDTO:
    authors: str
    title: str
    email: str

@dataclass
class ThesisScheduleDTO:
    id: int
    speaker_name: str
    title: str

    def to_dict(self):
        return {
            "id": self.id,
            "speaker_name": self.speaker_name,
            "title": self.title
        }



@dataclass
class ConferenceDTO:
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
    id: int
    title: str
    start_date: date
    end_date: date
    performance_time: int

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "performance_time": self.performance_time
        }



@dataclass
class FullApplicationDTO:
    id: int
    surname: str
    name: str
    patronymic: Optional[str]

    gender: str
    birth_date: date

    degree: str

    is_worker: bool
    is_student: bool

    work_name: Optional[str]
    work_place: Optional[str]
    work_position: Optional[str]

    study_name: Optional[str]
    study_place: Optional[str]
    study_level: Optional[str]

    participation_format: str
    email: str

    theses: list[ThesisInApplicationDTO]

    def to_dict(self):
        result = {
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

        return result

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
    surname: str
    name: str
    patronymic: Optional[str]

    gender: GenderEnum
    birth_date: date

    degree: DegreeEnum

    is_worker: bool
    is_student: bool

    work_name: Optional[str]
    work_place: Optional[str]
    work_position: Optional[str]

    study_name: Optional[str]
    study_place: Optional[str]
    study_level: Optional[EducationEnum]

    participation_format: ParticipationFormatEnum
    email: str

@dataclass
class FullScheduleDTO:
    conference: ConferenceScheduleDTO
    applications: List[ThesisScheduleDTO]
    schedule: List[dict]

    def to_dict(self):
        return {
            "conference": self.conference.to_dict(),
            "applications": [app.to_dict() for app in self.applications],
            "schedule": self.schedule
        }

@dataclass
class ConferenceFileDTO:
    title: str

@dataclass
class ScheduleItemDTO:
    item_type: ScheduleItemType
    global_order: int

    day_date: Optional[date] = None
    day_title: Optional[str] = None
    day_start_time: Optional[str] = None

    application_id: Optional[int] = None
    talk_speaker: Optional[str] = None
    talk_title: Optional[str] = None
    talk_duration: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    break_title: Optional[str] = None
    break_duration: Optional[int] = None

    text_content: Optional[str] = None

@dataclass
class ScheduleDTO:
    schedule: List[ScheduleItemDTO]