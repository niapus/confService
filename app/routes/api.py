import logging
import os

from flask import Blueprint, request, send_from_directory, jsonify, g

from app.decorator.handle_api_errors import require_admin_api, handle_api_errors
from app.dto_builders.dto_builder import build_schedule_dto
from app.utils.dependencies import get_application_service, get_schedule_service, get_log_service

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@api_bp.get('/log-files')
@handle_api_errors
@require_admin_api
def get_log_files():
    files = get_log_service().get_log_files()
    return jsonify(files)


@api_bp.get('/logs')
@handle_api_errors
@require_admin_api
def get_logs():
    filename = request.args.get('file', 'app.log')
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 100, type=int)
    lines = get_log_service().read_logs(filename, limit=limit, offset=offset)
    return jsonify({'lines': lines, 'offset': offset, 'limit': limit})


@api_bp.get('/download-log')
@handle_api_errors
@require_admin_api
def download_log():
    filename = request.args.get('file')
    filepath = get_log_service().get_file_path(filename)
    return send_from_directory(
        directory=os.path.dirname(filepath),
        path=filename,
        as_attachment=True,
        download_name=filename
    )


@api_bp.get('/conferences/<int:conf_id>')
@handle_api_errors
@require_admin_api
def get_full_applications(conf_id: int):
    full_applications = get_application_service().get_full_applications_for_conference(conf_id, g.db)
    return jsonify({
        'conference_id': conf_id,
        'applications': [app.to_dict() for app in full_applications]
    })


@api_bp.get('/conferences/<int:conf_id>/schedule-data')
@handle_api_errors
@require_admin_api
def get_schedule_data(conf_id: int):
    full_schedule = get_schedule_service().get_full_schedule_data(conf_id, g.db)
    return jsonify(full_schedule.to_dict())


@api_bp.post('/schedule')
@handle_api_errors
@require_admin_api
def update_schedule():
    json = request.get_json()
    schedule_dto = build_schedule_dto(json)
    get_schedule_service().update_schedule(schedule_dto, json.get('conference_id'), g.db)
    return jsonify({'success': True}), 200
