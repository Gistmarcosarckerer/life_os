from flask import Blueprint, jsonify, request

from backend.database import session_scope
from backend.services.mobile_entry_service import get_telegram_debug, list_recent_mobile_entries
from backend.services.nlp_service import list_raw_entries
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


@telegram_bp.route("/telegram/debug")
def telegram_debug():
    limit = request.args.get("limit", 8, type=int)
    limit = max(1, min(limit, 30))
    with session_scope() as session:
        debug = get_telegram_debug(session, limit=limit)
    return jsonify(debug)


@telegram_bp.route("/telegram/raw-entries")
def telegram_raw_entries():
    limit = request.args.get("limit", 20, type=int)
    limit = max(1, min(limit, 80))
    with session_scope() as session:
        entries = list_raw_entries(session, limit=limit)
    return jsonify(entries)
