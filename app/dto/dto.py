from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class ThesisInApplicationDTO:
    id: Optional[int]
    title: Optional[str]
    file_path: Optional[str]
    file_name: Optional[str]
    status: Optional[str]

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'status': self.status
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

    thesis_info: Optional[ThesisInApplicationDTO]

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
            'email': self.email
        }

        if self.thesis_info:
            result['thesis'] = self.thesis_info.to_dict()
        else:
            result['thesis'] = None

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