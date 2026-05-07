from flask_mail import Mail

from app.infrastructure.impl.flask_mailer import FlaskMailer
from app.mapper.application_mapper import ApplicationMapper
from app.mapper.schedule_mapper import ScheduleMapper
from app.repository.admin_repository import AdminRepository
from app.repository.application_repository import ApplicationRepository
from app.repository.conference_file_repository import ConferenceFileRepository
from app.repository.conference_repository import ConferenceRepository
from app.repository.email_repository import EmailRepository
from app.repository.schedule_repository import ScheduleRepository
from app.repository.thesis_repository import ThesisRepository
from app.service.admin_service import AdminService
from app.service.application_service import ApplicationService
from app.service.async_email_service import AsyncEmailService
from app.service.conference_file_service import ConferenceFileService
from app.service.conference_service import ConferenceService
from app.service.email_queue_service import EmailQueueService
from app.service.email_service import EmailService
from app.service.file_service import FileService
from app.service.jwt_service import JWTService
from app.service.log_service import LogService
from app.service.markdown_service import MarkdownService
from app.service.notification_service import NotificationService
from app.service.schedule_service import ScheduleService
from app.service.thesis_service import ThesisService
from app.service.verification_service import VerificationService


class AppServices:
    def __init__(self, app):
        self._app = app
        self._services = {}
        self.__repo = {}
        self.__mapper = {}
        self._init_app(app)

    def _init_app(self, app):
        self._init_mapper()
        self._init_repository()
        self._init_services(app)

    def _init_services(self, app):
        self._services['file'] = FileService(
            upload_folder=app.config['UPLOAD_FOLDER'],
            thesis_allowed_extensions=app.config['THESIS_ALLOWED_EXTENSIONS'],
            thesis_max_size=app.config['THESIS_CONTENT_LENGTH'],
            proceedings_allowed_extensions=app.config['PROCEEDINGS_ALLOWED_EXTENSIONS'],
            proceedings_max_size=app.config['PROCEEDINGS_CONTENT_LENGTH'],
            conference_file_allowed_extensions=app.config['CONFERENCE_FILE_ALLOWED_EXTENSIONS'],
            conference_file_max_size=app.config['CONFERENCE_FILE_CONTENT_LENGTH']
        )
        self._services['md'] = MarkdownService()

        self._services['jwt'] = JWTService(secret=app.config["SECRET_KEY"])

        email_queue_service = EmailQueueService(self.__repo['email'])

        mail_enabled = app.config['MAIL_ENABLED']
        verification_enabled = app.config['EMAIL_VERIFICATION_ENABLED']

        mail = Mail(app)
        flask_mailer = FlaskMailer(mail)
        email_service = EmailService(flask_mailer, app.config['MAIL_DEFAULT_SENDER'])

        self._services['email'] = AsyncEmailService(email_service, email_queue_service)
        self._services['notification'] = NotificationService(email_queue_service, mail_enabled, verification_enabled)

        self._services['admin'] = AdminService(
            self.__repo['admin']
        )

        self._services['conference'] = ConferenceService(
            self.__repo['conference'],
            self._services['md'],
            self._services['notification']
        )

        self._services['application'] = ApplicationService(
            self._services['conference'],
            self.__repo['application'],
            self.__mapper['application'],
            verification_enabled
        )

        self._services['verification'] = VerificationService(
            self._services['application'],
            self._services['jwt']
        )

        self._services['thesis'] = ThesisService(
            self._services['conference'],
            self._services['application'],
            self._services['file'],
            self.__repo['thesis']
        )

        self._services['schedule'] = ScheduleService(
            self._services['conference'],
            self._services['thesis'],
            self.__mapper['schedule'],
            self.__repo['schedule'],
            self._services['notification']
        )

        self._services['conference_file'] = ConferenceFileService(
            self._services['file'],
            self._services['conference'],
            self.__repo['conference_file']
        )

        self._services['log'] = LogService(
            logs_folder=app.config['LOGS_FOLDER']
        )

    def _init_repository(self):
        self.__repo['conference'] = ConferenceRepository()
        self.__repo['application'] = ApplicationRepository()
        self.__repo['thesis'] = ThesisRepository()
        self.__repo['admin'] = AdminRepository()
        self.__repo['conference_file'] = ConferenceFileRepository()
        self.__repo['schedule'] = ScheduleRepository()
        self.__repo['email'] = EmailRepository()

    def _init_mapper(self):
        self.__mapper['application'] = ApplicationMapper()
        self.__mapper['schedule'] = ScheduleMapper()

    @property
    def admin(self) -> AdminService:
        return self._services['admin']

    @property
    def conference(self) -> ConferenceService:
        return self._services['conference']

    @property
    def application(self) -> ApplicationService:
        return self._services['application']

    @property
    def thesis(self) -> ThesisService:
        return self._services['thesis']

    @property
    def email(self) -> AsyncEmailService:
        return self._services['email']

    @property
    def verification(self) -> VerificationService:
        return self._services['verification']

    @property
    def schedule(self) -> ScheduleService:
        return self._services['schedule']

    @property
    def conference_file(self) -> ConferenceFileService:
        return self._services['conference_file']

    @property
    def notification(self) -> NotificationService:
        return self._services['notification']

    @property
    def log(self) -> LogService:
        return self._services['log']