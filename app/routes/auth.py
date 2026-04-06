from flask import Blueprint, g, render_template, request, redirect, session as flask_session

from app.service import admin_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.get('/login')
def view_admin_login():
    return render_template('admin-login.html')

@auth_bp.post('/login')
def admin_login():
    admin = admin_service.authenticate(request.form.get("login"), request.form.get("password"), g.db)
    flask_session["admin_id"] = admin.id
    flask_session["admin_login"] = admin.login

    return redirect("/admin")