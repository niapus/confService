from sqlalchemy.orm import Session

from app.models.admin import Admin


class AdminRepository:
    """Доступ к данным администраторов."""

    def get_admin_count(self, session: Session) -> int:
        return session.query(Admin).count()

    def get_admin_by_login(self, login: str, session: Session) -> Admin | None:
        return session.query(Admin).filter_by(login=login).first()

    def save_all(self, admins: list[Admin], session: Session) -> None:
        session.add_all(admins)
