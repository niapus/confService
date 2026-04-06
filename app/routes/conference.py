from flask import Blueprint, render_template, request, g, redirect

from app.decorator.handle_form_errors import handle_form_errors
from app.dto_builders.dto_builder import build_application_dto, build_thesis_dto
from app.service import conference_service, application_service, thesis_service

from datetime import date


conference_bp = Blueprint("conference", __name__, url_prefix="/conference")

#Получить конференцию
@conference_bp.get('/<int:conf_id>')
def show_conference(conf_id):
    conference = conference_service.get_conference_by_id(conf_id, g.db)
    return render_template("conf-main.html", conference=conference, now=date.today())

@conference_bp.get(f'/<int:conf_id>/application')
def show_application(conf_id):
    conference_service.get_upcoming_conference(conf_id, g.db)
    return render_template("application.html")

@conference_bp.get(f'<int:conf_id>/thesis')
def show_upload_thesis(conf_id):
    conference_service.get_upcoming_conference(conf_id, g.db)
    return render_template("thesis.html", conf_id=conf_id)

@conference_bp.post(f'/<int:conf_id>/application')
@handle_form_errors("application.html")
def create_application(conf_id):
    dto = build_application_dto(request.form)
    application_service.create_application(conf_id, dto, g.db)
    return redirect(f'/conference/{conf_id}')

@conference_bp.post(f'<int:conf_id>/thesis')
@handle_form_errors("thesis.html", True)
def upload_thesis(conf_id):
    file = request.files.get('file')
    dto = build_thesis_dto(request.form)
    thesis_service.create_thesis(conf_id, file, dto, g.db)
    return redirect(f"/conference/{conf_id}")