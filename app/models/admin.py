from sqlalchemy import Column, Integer, String
from app.core.database import Base

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String, nullable=False)

    def __repr__(self):
        return f"Админ: имя {self.login}, id {self.id}"