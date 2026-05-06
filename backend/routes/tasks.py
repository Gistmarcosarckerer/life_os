from flask import Blueprint, jsonify, request

from backend.database import session_scope
from backend.services.task_service import (
    complete_task,
    create_task,
    delete_task,
    get_task_or_none,
    list_tasks,
    serialize_task,
    update_task,
)

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tasks", methods=["GET"])
def get_tasks():
    include_done = request.args.get("include_done", "true").lower() != "false"
    with session_scope() as session:
        tasks = list_tasks(session, include_done=include_done)
    return jsonify({"tasks": tasks})


@tasks_bp.route("/tasks", methods=["POST"])
def post_task():
    data = request.get_json(silent=True) or {}
    try:
        with session_scope() as session:
            task = create_task(session, data)
            payload = serialize_task(task)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(payload), 201


@tasks_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id: int):
    with session_scope() as session:
        task = get_task_or_none(session, task_id)
        if task is None:
            return jsonify({"error": "task not found"}), 404
        payload = serialize_task(task)
    return jsonify(payload)


@tasks_bp.route("/tasks/<int:task_id>", methods=["PUT", "PATCH"])
def patch_task(task_id: int):
    data = request.get_json(silent=True) or {}
    try:
        with session_scope() as session:
            task = get_task_or_none(session, task_id)
            if task is None:
                return jsonify({"error": "task not found"}), 404
            task = update_task(session, task, data)
            payload = serialize_task(task)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(payload)


@tasks_bp.route("/tasks/<int:task_id>/complete", methods=["POST"])
def post_complete_task(task_id: int):
    with session_scope() as session:
        task = get_task_or_none(session, task_id)
        if task is None:
            return jsonify({"error": "task not found"}), 404
        task = complete_task(session, task)
        payload = serialize_task(task)
    return jsonify(payload)


@tasks_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def remove_task(task_id: int):
    with session_scope() as session:
        task = get_task_or_none(session, task_id)
        if task is None:
            return jsonify({"error": "task not found"}), 404
        delete_task(session, task)
    return jsonify({"deleted": True, "id": task_id})
