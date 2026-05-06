from datetime import datetime, timedelta

from backend.models import ActivityLog


def get_focus_snapshot(session, window_minutes: int = 30) -> dict:
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    logs = (
        session.query(ActivityLog)
        .filter(ActivityLog.ended_at >= since)
        .order_by(ActivityLog.started_at.asc())
        .all()
    )

    productive_seconds = sum(
        log.duration_seconds for log in logs if log.category == "productive"
    )
    distraction_seconds = sum(
        log.duration_seconds for log in logs if log.category == "distraction"
    )
    neutral_seconds = sum(
        log.duration_seconds for log in logs if log.category == "neutral"
    )
    total_seconds = productive_seconds + distraction_seconds + neutral_seconds
    context_switches = sum(1 for log in logs if log.is_context_switch)
    active_log = logs[-1] if logs else None

    focus_score = calculate_focus_score(
        productive_seconds=productive_seconds,
        distraction_seconds=distraction_seconds,
        total_seconds=total_seconds,
        context_switches=context_switches,
        window_minutes=window_minutes,
    )
    state = detect_state(focus_score, context_switches, productive_seconds, total_seconds)

    return {
        "focus_score": focus_score,
        "state": state,
        "context_switches": context_switches,
        "productive_minutes": round(productive_seconds / 60, 2),
        "distraction_minutes": round(distraction_seconds / 60, 2),
        "neutral_minutes": round(neutral_seconds / 60, 2),
        "sample_count": len(logs),
        "window_minutes": window_minutes,
        "generated_at": datetime.utcnow().isoformat(),
        "current_activity": serialize_activity(active_log),
        "top_apps": get_top_apps(logs),
    }


def calculate_focus_score(
    productive_seconds: float,
    distraction_seconds: float,
    total_seconds: float,
    context_switches: int,
    window_minutes: int = 30,
) -> int:
    if total_seconds <= 0:
        return 50

    productive_ratio = productive_seconds / total_seconds
    distraction_ratio = distraction_seconds / total_seconds
    switch_pressure = min(context_switches / max(window_minutes / 3, 1), 1)

    score = 50
    score += productive_ratio * 45
    score -= distraction_ratio * 35
    score -= switch_pressure * 25

    return int(max(0, min(100, round(score))))


def detect_state(
    focus_score: int,
    context_switches: int,
    productive_seconds: float,
    total_seconds: float,
) -> str:
    productive_ratio = productive_seconds / total_seconds if total_seconds else 0

    if focus_score >= 75 and context_switches <= 4 and productive_ratio >= 0.65:
        return "flow"
    if focus_score < 45 or context_switches >= 12:
        return "disperso"
    return "normal"


def build_focus_recommendation(snapshot: dict, mission: dict | None) -> str:
    state = snapshot["state"]
    if mission is None:
        return "Cadastre uma tarefa para o sistema decidir a proxima missao."
    if state == "flow":
        return "Continue na missao atual e proteja os proximos 25 minutos."
    if state == "disperso":
        return "Reduza entradas: feche distracoes e execute apenas o primeiro passo da missao."
    return "Comece pela missao atual com um bloco curto de foco de 15 minutos."


def serialize_activity(log: ActivityLog | None) -> dict | None:
    if log is None:
        return None

    return {
        "id": log.id,
        "app_name": log.app_name,
        "window_title": log.window_title,
        "category": log.category,
        "started_at": log.started_at.isoformat() if log.started_at else None,
        "ended_at": log.ended_at.isoformat() if log.ended_at else None,
        "duration_seconds": round(log.duration_seconds, 2),
        "is_context_switch": log.is_context_switch,
    }


def get_top_apps(logs: list[ActivityLog], limit: int = 5) -> list[dict]:
    totals = {}
    for log in logs:
        app = log.app_name or "unknown"
        if app not in totals:
            totals[app] = {"app_name": app, "seconds": 0, "category": log.category}
        totals[app]["seconds"] += log.duration_seconds

    ranked = sorted(totals.values(), key=lambda item: item["seconds"], reverse=True)
    return [
        {
            "app_name": item["app_name"],
            "category": item["category"],
            "minutes": round(item["seconds"] / 60, 2),
        }
        for item in ranked[:limit]
    ]
