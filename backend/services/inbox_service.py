import json
from datetime import datetime

from backend.models import PersonalRule, RawEntry, Task
from backend.services.finance_service import categorize_transaction, create_transaction, money_value


VALID_REVIEW_STATUS = {"pending", "reviewed", "ignored"}
VALID_ACTIONS = {
    "confirm",
    "ignore",
    "create_transaction",
    "create_task",
    "create_rule",
    "mark_note",
}


def get_inbox_summary(session) -> dict:
    pending = session.query(RawEntry).filter(RawEntry.review_status == "pending").count()
    reviewed = session.query(RawEntry).filter(RawEntry.review_status == "reviewed").count()
    ignored = session.query(RawEntry).filter(RawEntry.review_status == "ignored").count()
    rules = session.query(PersonalRule).filter(PersonalRule.is_active == True).count()  # noqa: E712
    return {
        "pending": pending,
        "reviewed": reviewed,
        "ignored": ignored,
        "active_rules": rules,
        "recommendation": build_inbox_recommendation(pending, rules),
    }


def list_inbox_items(session, review_status: str = "pending", limit: int = 30) -> list[dict]:
    query = session.query(RawEntry)
    if review_status != "all":
        query = query.filter(RawEntry.review_status == normalize_review_status(review_status))
    entries = query.order_by(RawEntry.created_at.desc()).limit(limit).all()
    return [serialize_inbox_item(entry) for entry in entries]


def review_inbox_item(session, entry_id: int, data: dict) -> dict:
    entry = session.query(RawEntry).filter(RawEntry.id == entry_id).first()
    if entry is None:
        raise ValueError("Entrada nao encontrada.")

    action = str(data.get("action", "confirm") or "confirm").strip()
    if action not in VALID_ACTIONS:
        raise ValueError("Acao de inbox invalida.")

    result = {"action": action, "created": None}
    if action == "ignore":
        mark_entry(entry, "ignored", "ignored")
    elif action == "confirm":
        mark_entry(entry, "reviewed", "confirmed")
    elif action == "mark_note":
        mark_entry(entry, "reviewed", "note")
    elif action == "create_transaction":
        result["created"] = create_transaction_from_entry(session, entry, data)
        mark_entry(entry, "reviewed", "transaction")
    elif action == "create_task":
        result["created"] = create_task_from_entry(session, entry, data)
        mark_entry(entry, "reviewed", "task")
    elif action == "create_rule":
        result["created"] = create_rule_from_entry(session, entry, data)
        mark_entry(entry, "reviewed", "rule")

    session.flush()
    session.refresh(entry)
    result["entry"] = serialize_inbox_item(entry)
    return result


def list_personal_rules(session) -> list[dict]:
    rules = session.query(PersonalRule).order_by(PersonalRule.created_at.desc()).all()
    return [serialize_rule(rule) for rule in rules]


def create_personal_rule(session, data: dict) -> dict:
    pattern = required_text(data.get("pattern"), "pattern")
    rule = PersonalRule(
        name=str(data.get("name") or pattern).strip(),
        pattern=pattern.lower(),
        target_type=str(data.get("target_type") or "note").strip(),
        action=str(data.get("action") or "suggest").strip(),
        category=str(data.get("category") or "").strip(),
        priority=bounded_int(data.get("priority", 5), 1, 10),
        is_active=bool(data.get("is_active", True)),
    )
    session.add(rule)
    session.flush()
    session.refresh(rule)
    return serialize_rule(rule)


def apply_personal_rules_to_text(session, text: str) -> list[dict]:
    normalized = (text or "").lower()
    rules = (
        session.query(PersonalRule)
        .filter(PersonalRule.is_active == True)  # noqa: E712
        .order_by(PersonalRule.priority.desc())
        .all()
    )
    matches = []
    for rule in rules:
        if rule.pattern.lower() in normalized:
            matches.append(serialize_rule(rule))
    return matches


def serialize_inbox_item(entry: RawEntry) -> dict:
    extracted = {}
    try:
        extracted = json.loads(entry.extracted_data or "{}")
    except json.JSONDecodeError:
        extracted = {}

    return {
        "id": entry.id,
        "source": entry.source,
        "raw_text": entry.raw_text,
        "classification": entry.classification,
        "confidence": round(entry.confidence or 0, 3),
        "status": entry.status,
        "review_status": entry.review_status,
        "review_decision": entry.review_decision,
        "interpreted_text": entry.interpreted_text,
        "suggestion": entry.suggestion,
        "extracted_data": extracted,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "reviewed_at": entry.reviewed_at.isoformat() if entry.reviewed_at else None,
        "suggested_actions": suggest_actions(entry, extracted),
    }


def serialize_rule(rule: PersonalRule) -> dict:
    return {
        "id": rule.id,
        "name": rule.name,
        "pattern": rule.pattern,
        "target_type": rule.target_type,
        "action": rule.action,
        "category": rule.category,
        "priority": rule.priority,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


def create_transaction_from_entry(session, entry: RawEntry, data: dict) -> dict:
    extracted = safe_json(entry.extracted_data)
    amount = money_value(data.get("amount") or extracted.get("amount") or first_number(extracted))
    if amount <= 0:
        raise ValueError("Valor da transacao ausente.")

    transaction_type = str(
        data.get("transaction_type")
        or extracted.get("transaction_type")
        or ("income" if entry.classification == "financeiro" and extracted.get("entry_type") == "income" else "expense")
    )
    description = str(data.get("description") or extracted.get("description") or entry.raw_text).strip()
    category = str(data.get("category") or extracted.get("category") or categorize_transaction(description, transaction_type)).strip()

    transaction = create_transaction(
        session,
        amount=amount,
        description=description,
        transaction_type=transaction_type,
        category=category,
        source="inbox",
    )
    return {
        "type": "transaction",
        "id": transaction.id,
        "amount": transaction.amount,
        "transaction_type": transaction.transaction_type,
        "category": transaction.category,
    }


def create_task_from_entry(session, entry: RawEntry, data: dict) -> dict:
    extracted = safe_json(entry.extracted_data)
    task = Task(
        name=str(data.get("name") or extracted.get("name") or entry.raw_text).strip(),
        impact=bounded_int(data.get("impact") or extracted.get("impact") or 5, 1, 10),
        urgency=bounded_int(data.get("urgency") or extracted.get("urgency") or 5, 1, 10),
        energy_required=bounded_int(data.get("energy_required") or extracted.get("energy_required") or 5, 1, 10),
        status="pending",
    )
    session.add(task)
    session.flush()
    session.refresh(task)
    return {"type": "task", "id": task.id, "name": task.name}


def create_rule_from_entry(session, entry: RawEntry, data: dict) -> dict:
    payload = {
        "name": data.get("name") or f"Regra: {entry.raw_text[:32]}",
        "pattern": data.get("pattern") or entry.raw_text[:64],
        "target_type": data.get("target_type") or entry.classification,
        "action": data.get("rule_action") or "suggest",
        "category": data.get("category") or "",
        "priority": data.get("priority") or 5,
    }
    return {"type": "rule", **create_personal_rule(session, payload)}


def suggest_actions(entry: RawEntry, extracted: dict) -> list[str]:
    if entry.classification == "financeiro" or extracted.get("amount"):
        return ["confirm", "create_transaction", "create_rule", "ignore"]
    if entry.classification == "produtividade":
        return ["confirm", "create_task", "create_rule", "ignore"]
    if entry.status == "raw_input":
        return ["mark_note", "create_task", "create_transaction", "create_rule", "ignore"]
    return ["confirm", "create_rule", "ignore"]


def mark_entry(entry: RawEntry, status: str, decision: str) -> None:
    entry.review_status = normalize_review_status(status)
    entry.review_decision = decision
    entry.reviewed_at = datetime.utcnow()


def normalize_review_status(value: str) -> str:
    status = str(value or "pending").strip()
    return status if status in VALID_REVIEW_STATUS else "pending"


def build_inbox_recommendation(pending: int, rules: int) -> str:
    if pending == 0:
        return "Inbox limpa. O LIFE OS pode decidir com dados revisados."
    if pending >= 10:
        return "Ha muitas entradas pendentes. Revise primeiro as financeiras e tarefas."
    if rules == 0:
        return "Crie regras pessoais a partir das repeticoes para reduzir revisao manual."
    return "Revise entradas pendentes para melhorar as proximas decisoes."


def safe_json(value: str) -> dict:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def first_number(extracted: dict) -> float:
    numbers = extracted.get("numbers") or []
    if not numbers:
        return 0
    return money_value(numbers[0])


def required_text(value, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} e obrigatorio.")
    return text


def bounded_int(value, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return minimum
    return max(minimum, min(number, maximum))
