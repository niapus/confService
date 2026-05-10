import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ApplicationStatus(enum.Enum):
    """Статус заявки - подтверждена или не подтверждена."""

    CONFIRMED = "confirmed"
    UNCONFIRMED = "unconfirmed"


class DegreeEnum(enum.Enum):
    """Учёная степень участника."""

    NONE = "none"
    CANDIDATE = "candidate"
    DOCTOR = "doctor"


class EducationEnum(enum.Enum):
    """Уровень образования участника."""

    BACHELOR = "bachelor"
    SPECIALIST = "education_spec"
    MASTER = "education_mag"
    POSTGRADUATE = "education_asp"


class ParticipationFormatEnum(enum.Enum):
    """Формат участия в конференции."""

    OFFLINE = "offline"
    ONLINE = "online"


class GenderEnum(enum.Enum):
    """Пол участника."""

    MALE = "male"
    FEMALE = "female"


class Application(Base):
    """Заявка участника на участие в конференции."""

    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint('conference_id', 'email', name='uq_application_conference_email'),
    )

    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey("conferences.id", ondelete="CASCADE"), nullable=False, index=True)

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
    email = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.UNCONFIRMED, index=True)

    conference = relationship(
        "Conference",
        back_populates="applications"
    )

    theses = relationship(
        "Thesis",
        back_populates="application",
        cascade="all, delete-orphan"
    )