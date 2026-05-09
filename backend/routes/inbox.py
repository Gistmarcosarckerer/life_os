from flask import Blueprint, jsonify, render_template, request

from backend.database import session_scope
from backend.services.inbox_service import (
    create_personal_rule,
    get_inbox_summary,
    list_inbox_items,
    list_personal_rules,
    review_inbox_item,
)

inbox_bp = Blueprint("inbox", __name__)


@inbox_bp.route("/inbox")
def inbox_page():
    return render_template("inbox.html")


@inbox_bp.route("/api/inbox/summary")
def api_inbox_summary():
    with session_scope() as session:
        summary = get_inbox_summary(session)
    return jsonify(summary)


@inbox_bp.route("/api/inbox/items")
def api_inbox_items():
    status = request.args.get("status", "pending")
    limit = request.args.get("limit", 30, type=int)
    limit = max(1, min(limit, 100))
    with session_scope() as session:
        items = list_inbox_items(session, review_status=status, limit=limit)
    return jsonify({"items": items})


@inbox_bp.route("/api/inbox/items/<int:entry_id>/review", methods=["POST"])
def api_review_inbox_item(entry_id: int):
    data = request.get_json(silent=True) or {}
    try:
        with session_scope() as session:
            result = review_inbox_item(session, entry_id, data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result)


@inbox_bp.route("/api/inbox/rules", methods=["GET", "POST"])
def api_inbox_rules():
    with session_scope() as session:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            try:
                rule = create_personal_rule(session, data)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            return jsonify(rule), 201
        rules = list_personal_rules(session)
    return jsonify({"rules": rules})
