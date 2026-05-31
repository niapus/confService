import enum

from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.core.database import Base


class ThesisStatus(enum.Enum):
    """Статус проверки тезисов администратором."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Thesis(Base):
    """Файл тезисов доклада, прикреплённый к заявке участника."""

    __tablename__ = "theses"

    id = Column(Integer, primary_key=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)

    authors = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)

    status = Column(Enum(ThesisStatus), nullable=False)

    application = relationship(
        "Application",
        back_populates="theses"
    )