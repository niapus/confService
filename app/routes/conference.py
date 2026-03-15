from werkzeug.utils import redirect

from app.core.database import Session
from flask import Blueprint, render_template, abort, request
from app.service import conference_service, application_service, thesis_service


conference_bp = Blueprint("conference", __name__, url_prefix="/conference")

#Получить конференцию
@conference_bp.get('/<int:conf_id>')
def show_conference(conf_id):
    session = Session()
    conference = conference_service.get_conference_by_id(conf_id, session)
    session.close()
    return render_template("conf-main.html", conference=conference)

@conference_bp.get(f'/<int:conf_id>/application')
def show_application(conf_id):
    session = Session()
    conference = conference_service.get_conference_by_id(conf_id, session)
    session.close()
    return render_template("application.html", conference=conference)

@conference_bp.get(f'<int:conf_id>/thesis')
def show_upload_thesis(conf_id):
    session = Session()
    conference = conference_service.get_conference_by_id(conf_id, session)
    session.close()
    return render_template("thesis.html", conference=conference)

@conference_bp.post(f'/<int:conf_id>/application')
def create_application(conf_id):
    application_data = request.form
    session = Session()
    application = application_service.create_application(conf_id, application_data, session)
    return redirect(f'/conference/{conf_id}')

@conference_bp.post(f'<int:conf_id>/thesis')
def upload_thesis(conf_id):
    session = Session()
    file = request.files.get('file')
    data = request.form
    thesis_service.create_thesis(conf_id, file, data, session)
    session.close()
    return redirect(f"/conference/{conf_id}")