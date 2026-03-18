from flask import jsonify, Blueprint, render_template

from app.core.database import Session
from app.service import application_service

api_bp = Blueprint("api", __name__, url_prefix="/admin/api")

@api_bp.get('/conferences/<int:conf_id>')
def get_full_applications(conf_id):
    session = Session()
    full_applications = application_service.get_full_applications(conf_id, session)

    applications_data = [app.to_dict() for app in full_applications]
    session.close()

    return jsonify({
        'conference_id': conf_id,
        'applications': applications_data
    })

@api_bp.get('/conferences/<int:conf_id>/page')
def conference_page(conf_id):
    return render_template('conference_set.html', conf_id=conf_id)