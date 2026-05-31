import enum
from datetime import datetime

from sqlalchemy import Integer, Column, String, Text, DateTime, Enum, Index

from app.core.database import Base


class EmailStatus(enum.Enum):
    """Статус обработки письма в очереди."""

    PENDING = 'pending'
    FAILED = 'failed'


class QueueType(enum.Enum):
    """Тип очереди: массовая рассылка или индивидуальное письмо."""

    MASS = 'mass'
    INDIVIDUAL = 'individual'


class EmailQueue(Base):
    """Запись в очереди исходящих писем для асинхронной отправки."""

    __tablename__ = "email_queue"

    __table_args__ = (
        Index('ix_email_queue_status_type_created', 'status', 'queue_type', 'created_at'),
    )

    id = Column(Integer, primary_key=True, index=True)
    status = Column(Enum(EmailStatus), nullable=False, default=EmailStatus.PENDING)
    queue_type = Column(Enum(QueueType), nullable=False, default=QueueType.MASS)
    subject = Column(String(500), nullable=False)
    html_body = Column(Text, nullable=False)
    recipient = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    attempts = Column(Integer, nullable=False, default=0)
