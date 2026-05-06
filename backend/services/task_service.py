from datetime import datetime

from backend.models import Task


VALID_STATUSES = {"pending", "active", "done", "archived"}


def serialize_task(task: Task) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "impact": task.impact,
        "urgency": task.urgency,
        "energy_required": task.energy_required,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def list_tasks(session, include_done: bool = True) -> list[dict]:
    query = session.query(Task).order_by(Task.status.asc(), Task.urgency.desc())
    if not include_done:
        query = query.filter(Task.status.in_(["pending", "active"]))
    return [serialize_task(task) for task in query.all()]


def get_task_or_none(session, task_id: int) -> Task | None:
    return session.query(Task).filter(Task.id == task_id).first()


def create_task(session, data: dict) -> Task:
    name = _required_text(data, "name")
    task = Task(
        name=name,
        impact=_bounded_int(data.get("impact", 5), "impact"),
        urgency=_bounded_int(data.get("urgency", 5), "urgency"),
        energy_required=_bounded_int(data.get("energy_required", 5), "energy_required"),
        status=_valid_status(data.get("status", "pending")),
        created_at=datetime.utcnow(),
    )
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


def update_task(session, task: Task, data: dict) -> Task:
    if "name" in data:
        task.name = _required_text(data, "name")
    if "impact" in data:
        task.impact = _bounded_int(data["impact"], "impact")
    if "urgency" in data:
        task.urgency = _bounded_int(data["urgency"], "urgency")
    if "energy_required" in data:
        task.energy_required = _bounded_int(data["energy_required"], "energy_required")
    if "status" in data:
        task.status = _valid_status(data["status"])

    session.flush()
    session.refresh(task)
    return task


def complete_task(session, task: Task) -> Task:
    task.status = "done"
    session.flush()
    session.refresh(task)
    return task


def delete_task(session, task: Task) -> None:
    session.delete(task)
    session.flush()


def _required_text(data: dict, key: str) -> str:
    value = str(data.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _bounded_int(value, field: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a number") from exc

    if number < 1 or number > 10:
        raise ValueError(f"{field} must be between 1 and 10")
    return number


def _valid_status(value) -> str:
    status = str(value or "").strip().lower()
    if status not in VALID_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
    return status
