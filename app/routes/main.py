from flask import Blueprint, render_template, g
from app.service import conference_service
from datetime import date, datetime

main_bp = Blueprint("main", __name__)

@main_bp.get('/')
def show_main():
    conferences_future = conference_service.get_future_conferences(g.db)
    conferences_past = conference_service.get_past_conferences(g.db)
    return render_template("main2.html", conferences_future=conferences_future,
                           conferences_past=conferences_past, now=datetime.now())