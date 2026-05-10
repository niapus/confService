from datetime import date

from flask import Blueprint, render_template, request, g, redirect

from app.decorator.handle_form_errors import handle_form_errors
from app.dto_builders.dto_builder import build_application_dto, build_thesis_dto
from app.utils.dependencies import (
    get_conference_service, get_application_service, get_thesis_service,
    get_verification_service, get_notification_service, get_schedule_service
)

conference_bp = Blueprint("conference", __name__, url_prefix="/conference")


@conference_bp.get('/<int:conf_id>')
def show_conference(conf_id: int):
    conference = get_conference_service().get_conference_by_id(conf_id, g.db)
    schedule = get_schedule_service().get_schedule(conf_id, g.db)
    return render_template("conf-main.html",
                           conference=conference,
                           schedule_items=schedule,
                           now=date.today())


@conference_bp.get('/<int:conf_id>/application')
def show_application(conf_id: int):
    get_conference_service().check_registration_open(conf_id, g.db)
    return render_template("application.html")


@conference_bp.get('/<int:conf_id>/thesis')
def show_upload_thesis(conf_id: int):
    get_conference_service().check_submission_open(conf_id, g.db)
    return render_template("thesis.html", conf_id=conf_id)


@conference_bp.post('/<int:conf_id>/application')
@handle_form_errors("application.html")
def create_application(conf_id: int):
    dto = build_application_dto(request.form)
    application = get_application_service().create_application(conf_id, dto, g.db)
    notification = get_notification_service()

    if not notification.verification_enabled:
        return redirect(f'/conference/{conf_id}')

    conference = get_conference_service().get_conference_by_id(conf_id, g.db)
    token = get_verification_service().generate_verification_token(application)
    notification.send_verification_email(token, application, conference, g.db)
    return redirect(f'/conference/{conf_id}/application/verify')


@conference_bp.post('/<int:conf_id>/thesis')
@handle_form_errors("thesis.html", True)
def upload_thesis(conf_id: int):
    file = request.files.get('file')
    dto = build_thesis_dto(request.form)
    get_thesis_service().create_thesis(conf_id, file, dto, g.db)
    return redirect(f"/conference/{conf_id}")


@conference_bp.get('/<int:conf_id>/application/verify')
def verify_email(conf_id: int):
    return render_template("verify-email.html")
