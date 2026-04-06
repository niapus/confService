import os.path

from flask import Blueprint, render_template, request, redirect, g, send_from_directory, session as flask_session

from app.decorator.handle_form_errors import handle_form_errors
from app.dto_builders.dto_builder import build_conference_dto
from app.exceptions.auth_exception import ForbiddenException
from app.service import conference_service, thesis_service, application_service

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
def check_admin_auth():
    if not flask_session.get("admin_id"):
        raise ForbiddenException()

@admin_bp.get('/conferences/create')
def show_admin_create_conference():
    return render_template("conference_form.html", conference=None)

@admin_bp.post('/conferences/new')
@handle_form_errors("conference_form.html")
def create_conference():
    dto = build_conference_dto(request.form)
    conference_service.create_conference(dto, g.db)
    return redirect(f'/admin')

@admin_bp.get(f'/conferences/<int:conf_id>/edit')
def show_update_conference(conf_id):
    conference = conference_service.get_conference_by_id(conf_id, g.db)
    return render_template("conference_form.html", conference=conference)

@admin_bp.post(f'/conferences/<int:conf_id>/edit')
@handle_form_errors("conference_form.html")
def update_conference(conf_id):
    dto = build_conference_dto(request.form)
    conference_service.update_conference(conf_id, dto, g.db)
    return redirect(f'/admin')

@admin_bp.get('')
def show_admin_conferences():
    conferences = conference_service.get_all_conferences(g.db)
    theses = thesis_service.get_all_theses(g.db)
    applications = application_service.get_all_applications(g.db)
    return render_template("admin.html", theses=theses,
                               conferences=conferences, applications=applications)

@admin_bp.post(f'/theses/<int:thesis_id>/status')
def update_thesis_status(thesis_id):
    data = request.form
    thesis_service.update_thesis_status(thesis_id, data.get("status"), g.db)
    return redirect('/admin')

@admin_bp.post(f'/conferences/<int:conf_id>/delete')
def delete_conference(conf_id):
    thesis_service.delete_conference_theses_files(conf_id, g.db)
    conference_service.delete_conference(conf_id, g.db)
    return redirect('/admin')

@admin_bp.get('/conferences/<int:conf_id>')
def conference_page(conf_id):
    return render_template('conference_set.html', conf_id=conf_id)

@admin_bp.get(f'/thesis/<int:thesis_id>')
def view_thesis_file(thesis_id):
    thesis = thesis_service.get_thesis_by_id(thesis_id, g.db)
    dir_path = os.path.dirname(thesis.file_path)
    file_name = os.path.basename(thesis.file_path)
    return send_from_directory(dir_path, file_name, as_attachment=False)

@admin_bp.get(f'/applications/<int:thesis_id>')
def view_thesis_page(thesis_id):
    thesis = thesis_service.get_thesis_by_id(thesis_id, g.db)
    return render_template('thesis-data.html', thesis=thesis)