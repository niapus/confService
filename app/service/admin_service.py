from werkzeug.security import generate_password_hash, check_password_hash

from app.exceptions.auth_exception import InvalidCredentialsException
from app.models.admin import Admin


class AdminService:
    def __init__(self, admin_repository):
        self.__repo = admin_repository

    def create_admins_from_env(self, env_admin_data, session):
        if self.__repo.get_admin_count(session) != 0:
            return

        admins = []
        admins_data = env_admin_data.split(',')

        for data in admins_data:
            login, password = data.split(':', 1)

            admin = Admin(
                login=login,
                password_hash=generate_password_hash(password)
            )

            admins.append(admin)

        self.__repo.save_all(admins, session)

    def authenticate(self, login, password, session):
        admin = self.__repo.get_admin_by_login(login, session)

        if not admin:
            raise InvalidCredentialsException()

        if not check_password_hash(admin.password_hash, password):
            raise InvalidCredentialsException()

        return admin