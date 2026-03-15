from app.service.conference_service import ConferenceService
from app.service.application_service import ApplicationService
from app.service.thesis_service import ThesisService

conference_service = ConferenceService()
application_service = ApplicationService(conference_service)
thesis_service = ThesisService(conference_service, application_service)