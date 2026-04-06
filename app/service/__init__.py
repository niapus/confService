from app.service.conference_service import ConferenceService
from app.service.application_service import ApplicationService
from app.service.file_service import FileService
from app.service.thesis_service import ThesisService
from app.service.admin_service import AdminService

admin_service = AdminService()
conference_service = ConferenceService()
file_service = FileService()
application_service = ApplicationService(conference_service)
thesis_service = ThesisService(conference_service, application_service, file_service)