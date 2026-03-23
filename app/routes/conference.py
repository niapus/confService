from flask import Blueprint, render_template, abort, request, g, redirect

from app.dto_builders.dto_builder import build_application_dto
from app.service import conference_service, application_service, thesis_service


conference_bp = Blueprint("conference", __name__, url_prefix="/conference")

#Получить конференцию
@conference_bp.get('/<int:conf_id>')
def show_conference(conf_id):
    conference = conference_service.get_conference_by_id(conf_id, g.db)
    return render_template("conf-main.html", conference=conference)

@conference_bp.get(f'/<int:conf_id>/application')
def show_application(conf_id):
    conference = conference_service.get_conference_by_id(conf_id, g.db)
    return render_template("application.html", conference=conference)

@conference_bp.get(f'<int:conf_id>/thesis')
def show_upload_thesis(conf_id):
    conference = conference_service.get_conference_by_id(conf_id, g.db)
    return render_template("thesis.html", conference=conference)

@conference_bp.post(f'/<int:conf_id>/application')
def create_application(conf_id):
    dto = build_application_dto(request.form)
    application_service.create_application(conf_id, dto, g.db)
    return redirect(f'/conference/{conf_id}')

@conference_bp.post(f'<int:conf_id>/thesis')
def upload_thesis(conf_id):
    file = request.files.get('file')
    data = request.form
    thesis_service.create_thesis(conf_id, file, data, g.db)
    return redirect(f"/conference/{conf_id}")