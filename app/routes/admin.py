import logging
import os.path

from flask import Blueprint, render_template, request, redirect, g, \
    current_app, send_from_directory, session as flask_session

from app.decorator.handle_form_errors import handle_form_errors
from app.dto_builders.dto_builder import build_conference_dto, build_file_dto
from app.exceptions.auth_exception import ForbiddenException
from app.models.conference_file import ConferenceFileType
from app.utils.dependencies import get_conference_service, get_thesis_service, get_application_service, \
    get_conference_file_service, get_notification_service

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
logger = logging.getLogger(__name__)

@admin_bp.before_request
def check_admin_auth():
    if not flask_session.get("admin_id"):
        raise ForbiddenException()

#=========================Эндпоинты для конференций=============================
#GET==============
@admin_bp.get('/conferences/create')
def show_admin_create_conference():
    return render_template("conference_form.html", conference=None)

@admin_bp.get(f'/conferences/<int:conf_id>/edit')
def show_update_conference(conf_id):
    conference = get_conference_service().get_conference_by_id(conf_id, g.db)
    return render_template("conference_form.html", conf_id=conf_id, conference=conference)

@admin_bp.get('')
def show_admin_conferences():
    conferences = get_conference_service().get_all_conferences(g.db)
    theses = get_thesis_service().get_all_theses(g.db)
    applications = get_application_service().get_all_applications(g.db)
    return render_template("admin.html", theses=theses,
                               conferences=conferences, applications=applications)

@admin_bp.get('/conferences/<int:conf_id>')
def conference_page(conf_id):
    get_conference_service().exists(conf_id, g.db)
    return render_template('conference_set.html', conf_id=conf_id)

#POST==============
@admin_bp.post('/conferences/new')
@handle_form_errors("conference_form.html")
def create_conference():
    dto = build_conference_dto(request.form)
    conference = get_conference_service().create_conference(dto, g.db)

    admin_id = flask_session.get("admin_id")
    admin_login = flask_session.get("admin_login")

    logger.info("Админ id=%s, login=%s создал конференцию id=%s, title='%s'",
                admin_id, admin_login, conference.id, conference.title)
    return redirect(f'/admin')

@admin_bp.post(f'/conferences/<int:conf_id>/edit')
@handle_form_errors("conference_form.html", True)
def update_conference(conf_id):
    dto = build_conference_dto(request.form)
    conference = get_conference_service().update_conference(conf_id, dto, g.db)

    admin_id = flask_session.get("admin_id")
    admin_login = flask_session.get("admin_login")

    logger.info("Админ id=%s, login=%s обновил конференцию id=%s, title='%s'",
                admin_id, admin_login, conference.id, conference.title)
    return redirect(f'/admin')

@admin_bp.post(f'/conferences/<int:conf_id>/delete')
def delete_conference(conf_id):
    conference = get_conference_service().get_conference_by_id(conf_id, g.db)
    conf_title = conference.title
    conf_id_log = conference.id
    get_thesis_service().delete_all_conference_theses_files(conf_id, g.db)
    get_conference_file_service().delete_all_conference_files(conf_id, g.db)
    get_conference_service().delete_conference(conference, g.db)

    admin_id = flask_session.get("admin_id")
    admin_login = flask_session.get("admin_login")

    logger.warning("⚠ Админ id=%s, login=%s удалил конференцию id=%s, title=%s",
                    admin_id, admin_login, conf_id_log, conf_title)
    return redirect('/admin')

#=========================Эндпоинты для файлов==============================
@admin_bp.post(f'/conferences/<int:conf_id>/upload/proceedings')
def upload_proceedings(conf_id):
    dto = build_file_dto(request.form)
    file = request.files.get('file')
    get_conference_file_service().create_conference_file(file, dto, conf_id, ConferenceFileType.PROCEEDINGS, g.db)
    return redirect(f'/admin/conferences/{conf_id}/edit')

@admin_bp.post(f'/conferences/<int:conf_id>/upload/file')
def upload_file(conf_id):
    dto = build_file_dto(request.form)
    file = request.files.get('file')
    get_conference_file_service().create_conference_file(file, dto, conf_id, ConferenceFileType.CONFERENCE_FILE, g.db)
    return redirect(f'/admin/conferences/{conf_id}/edit')

@admin_bp.get('/conferences/files/<int:file_id>/view')
def view_conference_file(file_id):
    conf_file = get_conference_file_service().get_file_by_id(file_id, g.db)
    directory = os.path.join(current_app.config.get("UPLOAD_FOLDER"), os.path.dirname(conf_file.file_path))
    filename = os.path.basename(conf_file.file_path)
    return send_from_directory(directory, filename, as_attachment=False, download_name=conf_file.original_name)

@admin_bp.post(f'/conferences/<int:conf_id>/files/<int:file_id>/delete')
def delete_conference_file(conf_id, file_id):
    get_conference_file_service().delete_conference_file(file_id, g.db)
    return redirect(f'/admin/conferences/{conf_id}/edit')

@admin_bp.get(f'/thesis/<int:thesis_id>/view')
def view_thesis_file(thesis_id):
    thesis = get_thesis_service().get_thesis_by_id(thesis_id, g.db)
    directory = os.path.join(current_app.config.get("UPLOAD_FOLDER"), os.path.dirname(thesis.file_path))
    filename = os.path.basename(thesis.file_path)
    return send_from_directory(directory, filename, as_attachment=False, download_name=thesis.file_name)

#=========================Остальные==============================

@admin_bp.post(f'/theses/<int:thesis_id>/status')
def update_thesis_status(thesis_id):
    data = request.form
    thesis = get_thesis_service().update_thesis_status(thesis_id, data.get("status"), g.db)
    notification = get_notification_service()
    if notification.mail_enabled:
        notification.send_thesis_status(thesis, g.db)

    admin_id = flask_session.get("admin_id")
    admin_login = flask_session.get("admin_login")

    logger.info("Админ id=%s, login=%s изменил статус тезиса id=%s, title=%s на %s",
                 admin_id, admin_login, thesis.id, thesis.title, thesis.status.value)
    return redirect('/admin')

@admin_bp.get(f'/applications/<int:app_id>/thesis/<int:thesis_id>')
def view_thesis_page(app_id, thesis_id):
    thesis = get_thesis_service().get_thesis_by_id(thesis_id, g.db)
    return render_template('thesis-data.html', thesis=thesis)

@admin_bp.get('/logout')
def logout():
    admin_id = flask_session.get("admin_id")
    admin_login = flask_session.get("admin_login")

    logger.info("Админ вышел: id=%s, login=%s",
                admin_id, admin_login)
    flask_session.clear()
    return redirect("/")

@admin_bp.get(f'/conferences/<int:conf_id>/schedule')
def view_schedule_page(conf_id):
    get_conference_service().exists(conf_id, g.db)
    return render_template("shed.html")

@admin_bp.get('/logs')
def view_logs():
    return render_template('admin_logs.html')