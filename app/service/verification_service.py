from sqlalchemy.orm import Session

from app.exceptions.email_verification_exception import EmailVerificationException
from app.models.application import Application, ApplicationStatus
from app.service.application_service import ApplicationService
from app.service.jwt_service import JWTService


class VerificationService:
    """Верификация email-адреса участника через JWT-токен."""

    def __init__(self, application_service: ApplicationService, jwt_service: JWTService) -> None:
        self.__jwt_service = jwt_service
        self.__app_service = application_service

    def generate_verification_token(self, application: Application) -> str:
        """Генерирует JWT-токен для подтверждения email участника."""
        return self.__jwt_service.generate_verification_token(application.id, application.email)

    def verify_email(self, token: str, session: Session) -> Application:
        """Подтверждает email по токену. Выбрасывает EmailVerificationException при невалидном токене или повторном подтверждении."""
        payload = self.__jwt_service.verify_token(token)

        app_id = payload.get('app_id')
        email = payload.get('email')

        application = self.__app_service.get_by_id(app_id, session)

        if application.email != email:
            raise EmailVerificationException("Недействительная ссылка подтверждения")

        if application.status == ApplicationStatus.CONFIRMED:
            raise EmailVerificationException("Почта уже была подтверждена")

        self.__app_service.set_status(application, ApplicationStatus.CONFIRMED, session)

        return application
