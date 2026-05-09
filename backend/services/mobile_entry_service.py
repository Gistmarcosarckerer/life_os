from backend.models import BodyMetric, Expense, MobileEntry, MoodLog, TaskEntry


def serialize_mobile_entry(entry: MobileEntry) -> dict:
    return {
        "id": entry.id,
        "source": entry.source,
        "entry_type": entry.entry_type,
        "raw_text": entry.raw_text,
        "interpreted_text": entry.interpreted_text,
        "recommendation": entry.recommendation,
        "chat_id": entry.chat_id,
        "username": entry.username,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }


def list_recent_mobile_entries(session, limit: int = 10) -> list[dict]:
    entries = (
        session.query(MobileEntry)
        .order_by(MobileEntry.created_at.desc())
        .limit(limit)
        .all()
    )
    return [serialize_mobile_entry(entry) for entry in entries]


def create_mobile_entry(
    session,
    entry_type: str,
    raw_text: str,
    interpreted_text: str,
    recommendation: str = "",
    chat_id: str = "",
    username: str = "",
    source: str = "telegram",
) -> MobileEntry:
    entry = MobileEntry(
        source=source,
        entry_type=entry_type,
        raw_text=raw_text,
        interpreted_text=interpreted_text,
        recommendation=recommendation,
        chat_id=str(chat_id or ""),
        username=str(username or ""),
    )
    session.add(entry)
    session.flush()
    session.refresh(entry)
    return entry


def get_telegram_debug(session, limit: int = 10) -> dict:
    entries = list_recent_mobile_entries(session, limit=limit)
    latest = entries[0] if entries else None
    return {
        "chat_id": latest.get("chat_id", "") if latest else "",
        "username": latest.get("username", "") if latest else "",
        "messages": entries,
    }


def save_expense(session, amount: float, description: str) -> Expense:
    expense = Expense(amount=amount, description=description, source="telegram")
    session.add(expense)
    return expense


def save_body_metric(session, metric_type: str, value: float, unit: str) -> BodyMetric:
    metric = BodyMetric(
        metric_type=metric_type,
        value=value,
        unit=unit,
        source="telegram",
    )
    session.add(metric)
    return metric


def save_mood_log(session, mood=None, energy=None, anxiety=None) -> MoodLog:
    mood_log = MoodLog(
        mood=mood,
        energy=energy,
        anxiety=anxiety,
        source="telegram",
    )
    session.add(mood_log)
    return mood_log


def save_task_entry(
    session,
    name: str,
    entry_type: str = "task",
    status: str = "logged",
) -> TaskEntry:
    task_entry = TaskEntry(
        name=name,
        entry_type=entry_type,
        status=status,
        source="telegram",
    )
    session.add(task_entry)
    return task_entry
