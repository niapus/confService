import logging

from flask import Blueprint, g, render_template, request, redirect, session as flask_session

from app.utils.dependencies import get_admin_service, get_verification_service, get_notification_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
logger = logging.getLogger(__name__)


@auth_bp.get('/login')
def view_admin_login():
    return render_template('admin-login.html')


@auth_bp.post('/login')
def admin_login():
    admin = get_admin_service().authenticate(
        request.form.get("login"), request.form.get("password"), g.db
    )
    flask_session["admin_id"] = admin.id
    flask_session["admin_login"] = admin.login
    flask_session.permanent = True
    logger.info("✅ Успешный вход админа: id=%s, login=%s, IP=%s",
                admin.id, admin.login, request.remote_addr)
    return redirect("/admin")


@auth_bp.get('/verify/<token>')
def verify_email(token: str):
    application = get_verification_service().verify_email(token, g.db)
    get_notification_service().send_registration_confirmed(application, g.db)
    return render_template("email-confirmed.html")
