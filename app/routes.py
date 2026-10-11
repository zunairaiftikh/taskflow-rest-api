from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import VALID_STATUSES, Task

bp = Blueprint("main", __name__)

MAX_TITLE_LENGTH = 200
CREATABLE_FIELDS = ("title", "description")
UPDATABLE_FIELDS = ("title", "description", "status")
SQLITE_MAX_INTEGER = 9223372036854775807


# ---------- Validation helpers (shared by several endpoints) ----------

def unsupported_fields_message(data, allowed_fields):
    """Return an error message if data has unknown keys, else None."""
    unsupported = [key for key in data if key not in allowed_fields]
    if unsupported:
        allowed = ", ".join(allowed_fields)
        return f"Unsupported field(s): {', '.join(unsupported)}. Allowed fields: {allowed}"
    return None


def validate_title(value):
    """Return (clean_title, None) if valid, or (None, error_message)."""
    if not isinstance(value, str) or not value.strip():
        return None, "'title' must be a non-blank string"
    clean = value.strip()
    if len(clean) > MAX_TITLE_LENGTH:
        return None, f"'title' must be at most {MAX_TITLE_LENGTH} characters"
    return clean, None


def validate_description(value):
    """Return an error message if the description is invalid, else None."""
    if value is not None and not isinstance(value, str):
        return "'description' must be a string or null"
    return None


def validate_status(value):
    """Return an error message if the status is invalid, else None."""
    if value not in VALID_STATUSES:
        allowed = ", ".join(VALID_STATUSES)
        return f"Invalid status '{value}'. Allowed values: {allowed}"
    return None

def find_task(task_id):
    """Return the task with this id, or None if it does not exist."""
    # SQLite integers stop at this value; a larger id cannot exist.
    if task_id > SQLITE_MAX_INTEGER:
        return None
    return db.session.get(Task, task_id)

# ---------- Endpoints ----------

@bp.get("/health")
def health():
    """Confirm the API is running."""
    return jsonify({"status": "ok", "message": "TaskFlow API is running"}), 200


@bp.post("/api/tasks")
def create_task():
    """Create a new task."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    problem = unsupported_fields_message(data, CREATABLE_FIELDS)
    if problem:
        return jsonify({"error": problem}), 400

    if "title" not in data:
        return jsonify({"error": "'title' is required"}), 400

    title, problem = validate_title(data["title"])
    if problem:
        return jsonify({"error": problem}), 400

    description = data.get("description")
    problem = validate_description(description)
    if problem:
        return jsonify({"error": problem}), 400

    task = Task(title=title, description=description)
    db.session.add(task)
    db.session.commit()

    return jsonify(task.to_dict()), 201


@bp.get("/api/tasks")
def list_tasks():
    """Return tasks, oldest first. Optionally filter with ?status=."""
    query = Task.query

    if "status" in request.args:
        status = request.args["status"]
        problem = validate_status(status)
        if problem:
            return jsonify({"error": problem}), 400
        query = query.filter_by(status=status)

    tasks = query.order_by(Task.id).all()
    return jsonify({"count": len(tasks), "tasks": [t.to_dict() for t in tasks]}), 200


@bp.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    """Return one task by its ID."""
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": f"Task with id {task_id} not found"}), 404
    return jsonify(task.to_dict()), 200


@bp.patch("/api/tasks/<int:task_id>")
def update_task(task_id):
    """Partially update a task. Only the fields sent are changed."""
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": f"Task with id {task_id} not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    if not data:
        return jsonify({"error": "Request body must contain at least one field to update"}), 400

    problem = unsupported_fields_message(data, UPDATABLE_FIELDS)
    if problem:
        return jsonify({"error": problem}), 400

    # Validate every supplied field first, collecting clean values.
    changes = {}

    if "title" in data:
        title, problem = validate_title(data["title"])
        if problem:
            return jsonify({"error": problem}), 400
        changes["title"] = title

    if "description" in data:
        problem = validate_description(data["description"])
        if problem:
            return jsonify({"error": problem}), 400
        changes["description"] = data["description"]

    if "status" in data:
        problem = validate_status(data["status"])
        if problem:
            return jsonify({"error": problem}), 400
        changes["status"] = data["status"]

    # Only now, with everything valid, change the task.
    for field, value in changes.items():
        setattr(task, field, value)
    db.session.commit()

    return jsonify(task.to_dict()), 200


@bp.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    """Delete a task by its ID."""
    task = find_task(task_id)
    if task is None:
        return jsonify({"error": f"Task with id {task_id} not found"}), 404

    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": f"Task {task_id} deleted", "id": task_id}), 200