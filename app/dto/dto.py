from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class ThesisInApplicationDTO:
    id: int
    authors: str
    title: str
    file_path: str
    file_name: str
    status: str

    def to_dict(self):
        return {
            'id': self.id,
            'authors': self.authors,
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