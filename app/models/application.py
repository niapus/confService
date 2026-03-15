from sqlalchemy.orm import relationship

from app.core.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date, Boolean

import enum

class DegreeEnum(enum.Enum):
    NONE = "none"
    CANDIDATE = "candidate"
    DOCTOR = "doctor"

class EducationEnum(enum.Enum):
    BACHELOR = "none"
    SPECIALIST = "education_spec"
    MASTER = "education_mag"
    POSTGRADUATE = "education_asp"

class ParticipationFormatEnum(enum.Enum):
    OFFLINE = "offline"
    ONLINE = "online"

class GenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey("conferences.id", ondelete="CASCADE"), nullable=False)

    surname = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    patronymic = Column(String(100))

    gender = Column(Enum(GenderEnum), nullable=False)
    birth_date = Column(Date, nullable=False)

    degree = Column(Enum(DegreeEnum), nullable=False, default=DegreeEnum.NONE)

    is_worker = Column(Boolean, nullable=False)
    is_student = Column(Boolean, nullable=False)

    work_name = Column(String(200))
    work_place = Column(String(200))
    work_position = Column(String(200))

    study_name = Column(String(200))
    study_place = Column(String(200))
    study_level = Column(Enum(EducationEnum))

    participation_format = Column(Enum(ParticipationFormatEnum), nullable=False)
    email = Column(String(100), nullable=False)