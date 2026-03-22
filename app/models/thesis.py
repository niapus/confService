from sqlalchemy.orm import relationship

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
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)

    authors = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)

    status = Column(Enum(ThesisStatus), nullable=False)

    application = relationship(
        "Application",
        back_populates="theses"
    )