from flask import Blueprint, jsonify, request

from backend.database import session_scope
from backend.models import RawEntry
from backend.services.activity_tracker import ActivityTracker
from backend.services.background_tracker import background_activity_tracker
from backend.services.decision_engine import choose_current_mission
from backend.services.finance_service import get_financial_summary, list_transactions
from backend.services.mobile_entry_service import create_mobile_entry
from backend.services.nlp_service import (
    analyze_message,
    apply_analysis,
    list_raw_entries,
    save_raw_entry,
)
from backend.services.productivity_engine import (
    build_focus_recommendation,
    get_focus_snapshot,
)
from backend.services.task_service import list_tasks

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


@productivity_bp.route("/api/summary")
def app_summary():
    with session_scope() as session:
        snapshot = get_focus_snapshot(session)
        mission = choose_current_mission(
            session,
            focus_score=snapshot["focus_score"],
            state=snapshot["state"],
        )
        finance = get_financial_summary(session)
        transactions = list_transactions(session, limit=12)
        tasks = list_tasks(session, include_done=False)[:8]
        raw_entries = list_raw_entries(session, limit=10)
        latest_raw = (
            session.query(RawEntry).order_by(RawEntry.created_at.desc()).first()
        )
        recommendation = build_focus_recommendation(snapshot, mission)

    return jsonify(
        {
            "focus": {
                "score": snapshot["focus_score"],
                "state": snapshot["state"],
                "recommendation": recommendation,
                "current_activity": snapshot["current_activity"],
                "top_apps": snapshot["top_apps"],
                "context_switches": snapshot["context_switches"],
                "productive_minutes": snapshot["productive_minutes"],
                "distraction_minutes": snapshot["distraction_minutes"],
            },
            "mission": mission,
            "finance": finance,
            "recentTransactions": transactions,
            "activeTasks": tasks,
            "recentEntries": raw_entries["entries"],
            "interpretedEntries": raw_entries["interpreted"],
            "unclassifiedEntries": raw_entries["unclassified"],
            "suggestions": raw_entries["suggestions"],
            "lastInputAt": latest_raw.created_at.isoformat() if latest_raw else None,
        }
    )


@productivity_bp.route("/api/smart-entry", methods=["POST"])
def smart_entry():
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Mensagem vazia."}), 400

    with session_scope() as session:
        analysis = analyze_message(text)
        raw_entry = save_raw_entry(
            session,
            analysis,
            username="dashboard",
            source="dashboard",
        )
        raw_entry_id = raw_entry.id
        apply_analysis(session, analysis, source="dashboard")
        create_mobile_entry(
            session,
            entry_type=analysis.entry_type,
            raw_text=analysis.raw_text,
            interpreted_text=analysis.interpreted_text,
            recommendation=analysis.suggestion,
            username="dashboard",
            source="dashboard",
        )
        finance = get_financial_summary(session)
        snapshot = get_focus_snapshot(session)
        mission = choose_current_mission(
            session,
            focus_score=snapshot["focus_score"],
            state=snapshot["state"],
        )

    return jsonify(
        {
            "ok": True,
            "entry_id": raw_entry_id,
            "classification": analysis.classification,
            "status": analysis.status,
            "confidence": round(float(analysis.confidence), 3),
            "interpreted_text": analysis.interpreted_text,
            "suggestion": analysis.suggestion,
            "mission": mission,
            "finance": {
                "projected_balance": finance["projected_balance"],
                "risk_level": finance["risk_level"],
                "recommendation": finance["recommendation"],
            },
        }
    )
