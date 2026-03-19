from flask import jsonify, Blueprint, g

from app.core.database import Session
from app.service import application_service

api_bp = Blueprint("api", __name__, url_prefix="/admin/api")

@api_bp.get('/conferences/<int:conf_id>')
def get_full_applications(conf_id):
    full_applications = application_service.get_full_applications(conf_id, g.db)

    applications_data = [app.to_dict() for app in full_applications]

    return jsonify({
        'conference_id': conf_id,
        'applications': applications_data
    })