from flask import Blueprint, jsonify

from backend.database import session_scope
from backend.services.activity_tracker import ActivityTracker
from backend.services.background_tracker import background_activity_tracker
from backend.services.decision_engine import choose_current_mission
from backend.services.productivity_engine import (
    build_focus_recommendation,
    get_focus_snapshot,
)

productivity_bp = Blueprint("productivity", __name__)


@productivity_bp.route("/state")
def get_state():
    with session_scope() as session:
        snapshot = get_focus_snapshot(session)
    return jsonify({"state": snapshot["state"]})


@productivity_bp.route("/track", methods=["POST"])
def track_activity():
    log = ActivityTracker().capture_once()
    return jsonify(
        {
            "id": log.id,
            "app_name": log.app_name,
            "window_title": log.window_title,
            "duration_seconds": log.duration_seconds,
            "category": log.category,
            "is_context_switch": log.is_context_switch,
        }
    )


@productivity_bp.route("/tracker-status")
def tracker_status():
    return jsonify(background_activity_tracker.status())


@productivity_bp.route("/life-status")
def life_status():
    with session_scope() as session:
        snapshot = get_focus_snapshot(session)
        mission = choose_current_mission(
            session,
            focus_score=snapshot["focus_score"],
            state=snapshot["state"],
        )
        recommendation = build_focus_recommendation(snapshot, mission)

    return jsonify(
        {
            "focus_score": snapshot["focus_score"],
            "estado_atual": snapshot["state"],
            "missao_atual": mission,
            "recomendacao": recommendation,
            "atividade_atual": snapshot["current_activity"],
            "top_apps": snapshot["top_apps"],
            "atualizado_em": snapshot["generated_at"],
            "metricas": {
                "trocas_contexto": snapshot["context_switches"],
                "minutos_produtivos": snapshot["productive_minutes"],
                "minutos_distracao": snapshot["distraction_minutes"],
                "minutos_neutros": snapshot["neutral_minutes"],
                "amostras": snapshot["sample_count"],
                "janela_minutos": snapshot["window_minutes"],
            },
        }
    )
