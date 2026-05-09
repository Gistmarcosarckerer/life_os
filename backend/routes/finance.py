from flask import Blueprint, jsonify, render_template, request

from backend.database import session_scope
from backend.services.finance_service import (
    create_goal,
    create_transaction,
    evaluate_purchase,
    get_financial_summary,
    get_or_create_profile,
    list_goals,
    list_transactions,
    serialize_profile,
    serialize_transaction,
    update_financial_profile,
)
from backend.services.pluggy_service import (
    PluggyError,
    create_connect_token,
    get_pluggy_status,
    list_bank_accounts,
    register_item,
    sync_all_connections,
    sync_connection,
)

finance_bp = Blueprint("finance", __name__)


@finance_bp.route("/finance")
def finance_page():
    return render_template("finance.html")


@finance_bp.route("/finance/settings", methods=["GET", "POST"])
def finance_settings():
    with session_scope() as session:
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form.to_dict()
            profile = update_financial_profile(session, data)
        else:
            profile = get_or_create_profile(session)
        payload = serialize_profile(profile)
    return jsonify(payload)


@finance_bp.route("/finance/transactions", methods=["GET", "POST"])
def finance_transactions():
    with session_scope() as session:
        if request.method == "POST":
            data = request.get_json(silent=True) or request.form.to_dict()
            transaction = create_transaction(
                session,
                amount=data.get("amount", 0),
                description=data.get("description", ""),
                transaction_type=data.get("transaction_type", "expense"),
                category=data.get("category") or None,
                source="dashboard",
            )
            payload = serialize_transaction(transaction)
            return jsonify(payload), 201

        limit = request.args.get("limit", 30, type=int)
        payload = list_transactions(session, limit=max(1, min(limit, 100)))
    return jsonify({"transactions": payload})


@finance_bp.route("/finance/purchase-check", methods=["POST"])
def finance_purchase_check():
    data = request.get_json(silent=True) or {}
    try:
        with session_scope() as session:
            result = evaluate_purchase(session, data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result)


@finance_bp.route("/finance/goals", methods=["GET", "POST"])
def finance_goals():
    with session_scope() as session:
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            try:
                goal = create_goal(session, data)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
            return jsonify(
                {
                    "id": goal.id,
                    "name": goal.name,
                    "goal_type": goal.goal_type,
                    "target_amount": goal.target_amount,
                    "current_amount": goal.current_amount,
                    "category": goal.category,
                    "status": goal.status,
                }
            ), 201

        goals = list_goals(session)
    return jsonify({"goals": goals})


@finance_bp.route("/api/finance/summary")
def api_finance_summary():
    with session_scope() as session:
        summary = get_financial_summary(session)
        transactions = list_transactions(session, limit=8)
        goals = list_goals(session)
        pluggy = get_pluggy_status(session)
        bank_accounts = list_bank_accounts(session)
    return jsonify(
        {
            "summary": summary,
            "transactions": transactions,
            "goals": goals,
            "pluggy": pluggy,
            "bank_accounts": bank_accounts,
        }
    )


@finance_bp.route("/finance/bank/status")
def finance_bank_status():
    with session_scope() as session:
        status = get_pluggy_status(session)
        accounts = list_bank_accounts(session)
    return jsonify({"pluggy": status, "bank_accounts": accounts})


@finance_bp.route("/finance/bank/connect-token", methods=["POST"])
def finance_bank_connect_token():
    webhook_url = request.url_root.rstrip("/") + "/finance/bank/webhook"
    try:
        token = create_connect_token(webhook_url=webhook_url, client_user_id="life-os-owner")
    except PluggyError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(token)


@finance_bp.route("/finance/bank/items", methods=["POST"])
def finance_bank_items():
    payload = request.get_json(silent=True) or {}
    try:
        with session_scope() as session:
            connection = register_item(session, payload)
            result = sync_connection(session, connection.item_id)
            status = get_pluggy_status(session)
            accounts = list_bank_accounts(session)
    except PluggyError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"connection": status, "bank_accounts": accounts, "sync": result}), 201


@finance_bp.route("/finance/bank/sync", methods=["POST"])
def finance_bank_sync():
    try:
        with session_scope() as session:
            result = sync_all_connections(session)
            status = get_pluggy_status(session)
            accounts = list_bank_accounts(session)
    except PluggyError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"sync": result, "pluggy": status, "bank_accounts": accounts})


@finance_bp.route("/finance/bank/webhook", methods=["POST"])
def finance_bank_webhook():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("itemId")
    if not item_id:
        return jsonify({"status": "ignored", "reason": "itemId ausente"}), 200
    try:
        with session_scope() as session:
            result = sync_connection(session, item_id)
    except PluggyError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    return jsonify({"status": "ok", "sync": result})
