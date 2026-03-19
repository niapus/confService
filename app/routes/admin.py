from flask import Blueprint, render_template, request, redirect, g

from app.service import conference_service, thesis_service

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.get('/conferences/create')
def show_admin_create_conference():
    return render_template("conference_form.html", conference=None)

@admin_bp.post('/conferences/new')
def create_conference():
    conf_data = request.form.to_dict()
    conference_service.create_conference(conf_data, g.db)
    return redirect(f'/admin')

@admin_bp.get(f'/conferences/<int:conf_id>/edit')
def show_update_conference(conf_id):
    conference = conference_service.get_conference_by_id(conf_id, g.db)
    return render_template("conference_form.html", conference=conference)

@admin_bp.post(f'/conferences/<int:conf_id>/edit')
def update_conference(conf_id):
    conf_data = request.form.to_dict()
    conference_service.update_conference(conf_id, conf_data, g.db)
    return redirect(f'/admin')

@admin_bp.get('')
def show_admin_conferences():
    conferences = conference_service.get_all_conferences(g.db)
    theses = thesis_service.get_all_theses(g.db)

    rendered = render_template("admin.html", theses=theses, conferences=conferences)
    return rendered

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