from app.exceptions.auth_exception import InvalidCredentialsException
from app.models.admin import Admin
from app.repository.admin_repository import AdminRepository
from werkzeug.security import generate_password_hash, check_password_hash


class AdminService():
    def __init__(self):
        self.__repo = AdminRepository()

    def create_default_admin(self, login, password, session):
        if self.__repo.get_admin_count(session) != 0:
            return

        admin = Admin(
            login=login,
            password_hash=generate_password_hash(password)
        )

        self.__repo.save(admin, session)

    def authenticate(self, login, password, session):
        admin = self.__repo.get_admin_by_login(login, session)

        if not admin:
            raise InvalidCredentialsException()

        if not check_password_hash(admin.password_hash, password):
            raise InvalidCredentialsException()

        return admin