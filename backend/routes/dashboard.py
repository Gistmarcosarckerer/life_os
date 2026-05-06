from flask import Blueprint, render_template

from backend.database import session_scope
from backend.services.decision_engine import choose_current_mission
from backend.services.finance_service import get_financial_summary
from backend.services.productivity_engine import get_focus_snapshot

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard():
    with session_scope() as session:
        snapshot = get_focus_snapshot(session)
        mission = choose_current_mission(
            session,
            focus_score=snapshot["focus_score"],
            state=snapshot["state"],
        )
        finance = get_financial_summary(session)

    return render_template(
        "dashboard.html",
        focus_score=snapshot["focus_score"],
        state=snapshot["state"],
        main_task=mission["name"] if mission else "Nenhuma missao cadastrada",
        finance=finance,
    )


@dashboard_bp.route("/productivity")
def productivity_page():
    return render_template("productivity.html")


@dashboard_bp.route("/telegram")
def telegram_page():
    return render_template("telegram.html")


@dashboard_bp.route("/gym")
def gym_page():
    return render_template("gym.html")


@dashboard_bp.route("/settings")
def settings_page():
    return render_template("settings.html")
