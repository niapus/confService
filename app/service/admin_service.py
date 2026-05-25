import secrets

from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from app.exceptions.auth_exception import InvalidCredentialsException
from app.models.admin import Admin
from app.repository.admin_repository import AdminRepository


class AdminService:
    """Управление учётными записями администраторов."""

    def __init__(self, admin_repository: AdminRepository) -> None:
        self.__repo = admin_repository

    def create_admins_from_env(self, env_admin_data: str, session: Session) -> None:
        """Создаёт администраторов из строки ADMIN_DATA, если таблица пуста.

        Args:
            env_admin_data: Строка вида ``login:password,login2:password2``.
        """
        if self.__repo.get_admin_count(session) != 0:
            return

        admins = []
        for data in env_admin_data.split(','):
            login, password = data.split(':', 1)
            admins.append(Admin(
                login=login,
                password_hash=generate_password_hash(password)
            ))

        self.__repo.save_all(admins, session)

    def create_default_admin_if_empty(self, session: Session) -> tuple[str, str] | None:
        """Создаёт админа "admin" со случайным паролем, если таблица пуста.

        Returns:
            Кортеж (login, password) при создании, None — если админы уже есть.
            Пароль возвращается plaintext один раз для показа организатору; в БД лежит хеш.
        """
        if self.__repo.get_admin_count(session) != 0:
            return None

        login = 'admin'
        password = secrets.token_urlsafe(12)

        self.__repo.save_all([Admin(
            login=login,
            password_hash=generate_password_hash(password)
        )], session)

        return login, password

    def authenticate(self, login: str, password: str, session: Session) -> Admin:
        """Проверяет логин и пароль. Выбрасывает InvalidCredentialsException при несоответствии."""
        admin = self.__repo.get_admin_by_login(login, session)

        if not admin:
            raise InvalidCredentialsException()

        if not check_password_hash(admin.password_hash, password):
            raise InvalidCredentialsException()

        return admin
