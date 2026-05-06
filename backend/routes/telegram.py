from flask import Blueprint, jsonify, request

from backend.database import session_scope
from backend.services.mobile_entry_service import list_recent_mobile_entries
from backend.services.telegram_bot import telegram_bot_service

telegram_bp = Blueprint("telegram", __name__)


@telegram_bp.route("/telegram/status")
def telegram_status():
    return jsonify(telegram_bot_service.status())


@telegram_bp.route("/telegram/entries")
def telegram_entries():
    limit = request.args.get("limit", 10, type=int)
    limit = max(1, min(limit, 50))
    with session_scope() as session:
        entries = list_recent_mobile_entries(session, limit=limit)
    return jsonify({"entries": entries})
