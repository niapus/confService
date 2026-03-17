from app.core.database import Session
from flask import Blueprint, render_template, request, redirect

from app.service import conference_service, thesis_service

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.get('/conferences/create')
def show_admin_create_conference():
    return render_template("conference_form.html", conference=None)

@admin_bp.post('/conferences/new')
def create_conference():
    session = Session()
    conf_data = request.form.to_dict()

    conference_service.create_conference(conf_data, session)
    session.close()
    return redirect(f'/admin')

@admin_bp.get(f'/conferences/<int:conf_id>/edit')
def show_update_conference(conf_id):
    session = Session()
    conference = conference_service.get_conference_by_id(conf_id, session)
    session.close()
    return render_template("conference_form.html", conference=conference)

@admin_bp.post(f'/conferences/<int:conf_id>/edit')
def update_conference(conf_id):
    conf_data = request.form.to_dict()
    session = Session()
    conference_service.update_conference(conf_id, conf_data, session)
    return redirect(f'/admin')

@admin_bp.get('')
def show_admin_conferences():
    session = Session()
    conferences = conference_service.get_all_conferences(session)
    theses = thesis_service.get_all_theses(session)

    rendered = render_template("admin.html", theses=theses, conferences=conferences)
    session.close()
    return rendered

@admin_bp.post(f'/theses/<int:thesis_id>/status')
def update_thesis_status(thesis_id):
    session = Session()
    data = request.form
    thesis_service.update_thesis_status(thesis_id, data.get("status"), session)
    session.close()
    return redirect('/admin')

@admin_bp.post(f'/conferences/<int:conf_id>/delete')
def delete_conference(conf_id):
    session = Session()
    thesis_service.delete_conference_theses_files(conf_id, session)
    conference_service.delete_conference(conf_id, session)
    session.close()
    return redirect('/admin')