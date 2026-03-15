from app.core.database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
import enum

class ThesisStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Thesis(Base):
    __tablename__ = "theses"

    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey("conferences.id"), nullable=False)

    surname = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    patronymic = Column(String(100))
    email = Column(String(100), nullable=False)

    title = Column(String(200), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)

    status = Column(Enum(ThesisStatus), nullable=False)

    @property
    def status_value(self):
        return self.status.value