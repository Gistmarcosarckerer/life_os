from backend.models import Task


def choose_current_mission(session, focus_score: int, state: str) -> dict | None:
    tasks = (
        session.query(Task)
        .filter(Task.status.in_(["pending", "active"]))
        .all()
    )
    if not tasks:
        return None

    scored_tasks = [
        {
            "id": task.id,
            "name": task.name,
            "impact": task.impact,
            "urgency": task.urgency,
            "energy_required": task.energy_required,
            "status": task.status,
            "score": calculate_task_score(task, focus_score, state),
        }
        for task in tasks
    ]
    mission = max(scored_tasks, key=lambda item: item["score"])
    sync_active_mission(session, mission["id"])
    mission["status"] = "active"
    return mission


def calculate_task_score(task: Task, focus_score: int, state: str) -> float:
    energy_capacity = infer_energy_capacity(focus_score, state)
    energy_fit = 10 - abs(task.energy_required - energy_capacity)
    overload_penalty = max(task.energy_required - energy_capacity, 0) * 1.8

    score = (task.impact * 3.0) + (task.urgency * 2.5) + (energy_fit * 1.6)
    score -= overload_penalty
    return round(max(score, 0), 2)


def infer_energy_capacity(focus_score: int, state: str) -> int:
    if state == "flow":
        return 9
    if state == "disperso":
        return 3
    if focus_score >= 65:
        return 7
    return 5


def sync_active_mission(session, mission_id: int) -> None:
    tasks = session.query(Task).filter(Task.status.in_(["pending", "active"])).all()
    for task in tasks:
        task.status = "active" if task.id == mission_id else "pending"
    session.flush()


def seed_default_tasks(session):
    has_tasks = session.query(Task.id).first()
    if has_tasks:
        return

    session.add_all(
        [
            Task(
                name="Definir a proxima decisao critica do LIFE OS",
                impact=9,
                urgency=8,
                energy_required=6,
                status="pending",
            ),
            Task(
                name="Executar bloco curto de manutencao cognitiva",
                impact=6,
                urgency=7,
                energy_required=3,
                status="pending",
            ),
            Task(
                name="Organizar backlog de automacoes pessoais",
                impact=7,
                urgency=5,
                energy_required=5,
                status="pending",
            ),
        ]
    )
