from datetime import date

from flask import Blueprint, render_template, g

from app.utils.dependencies import get_conference_service

main_bp = Blueprint("main", __name__)


@main_bp.get('/')
def show_main():
    conferences_future = get_conference_service().get_future_conferences(g.db)
    conferences_past = get_conference_service().get_past_conferences(g.db)
    return render_template("main.html",
                           conferences_future=conferences_future,
                           conferences_past=conferences_past,
                           now=date.today())
