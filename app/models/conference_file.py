import enum

from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class ConferenceFileType(enum.Enum):
    """Тип файла конференции: сборник тезисов или произвольный файл."""

    PROCEEDINGS = "proceedings"
    CONFERENCE_FILE = "conference_file"


class ConferenceFile(Base):
    """Файл, прикреплённый к конференции (сборник тезисов или справочный материал)."""

    __tablename__ = "conference_files"

    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey('conferences.id', ondelete='CASCADE'), index=True)

    file_type = Column(Enum(ConferenceFileType), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    title = Column(String(255), nullable=False)

    conference = relationship("Conference", back_populates="files")