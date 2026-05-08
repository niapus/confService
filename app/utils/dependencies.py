"""Вспомогательные функции для получения сервисов из Flask application context."""
from flask import current_app

from app.service.admin_service import AdminService
from app.service.application_service import ApplicationService
from app.service.conference_file_service import ConferenceFileService
from app.service.conference_service import ConferenceService
from app.service.log_service import LogService
from app.service.notification_service import NotificationService
from app.service.schedule_service import ScheduleService
from app.service.thesis_service import ThesisService
from app.service.verification_service import VerificationService


def get_services():
    return current_app.extensions['services']

def get_conference_service() -> ConferenceService:
    return get_services().conference

def get_application_service() -> ApplicationService:
    return get_services().application

def get_admin_service() -> AdminService:
    return get_services().admin

def get_thesis_service() -> ThesisService:
    return get_services().thesis

def get_conference_file_service() -> ConferenceFileService:
    return get_services().conference_file

def get_verification_service() -> VerificationService:
    return get_services().verification

def get_schedule_service() -> ScheduleService:
    return get_services().schedule

def get_notification_service() -> NotificationService:
    return get_services().notification

def get_log_service() -> LogService:
    return get_services().log