def create_task(client, title="Sample task", **fields):
    """Helper: create a task through the API and return its JSON."""
    response = client.post("/api/tasks", json={"title": title, **fields})
    assert response.status_code == 201
    return response.get_json()


# ---------- Health ----------

def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


# ---------- Create ----------

def test_create_task_success(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Learn pytest", "description": "Write the first tests"},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["title"] == "Learn pytest"
    assert data["description"] == "Write the first tests"
    assert data["status"] == "pending"
    assert data["created_at"].endswith("Z")
    assert data["updated_at"].endswith("Z")


def test_create_task_missing_title_returns_400(client):
    response = client.post("/api/tasks", json={"description": "no title"})

    assert response.status_code == 400
    assert "title" in response.get_json()["error"]


def test_create_task_blank_title_returns_400(client):
    response = client.post("/api/tasks", json={"title": "   "})

    assert response.status_code == 400
    assert "title" in response.get_json()["error"]


def test_create_task_unsupported_field_returns_400(client):
    response = client.post("/api/tasks", json={"title": "x", "colour": "red"})

    assert response.status_code == 400
    assert "colour" in response.get_json()["error"]


# ---------- List and filter ----------

def test_list_tasks_empty(client):
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == {"count": 0, "tasks": []}


def test_list_tasks_returns_all_in_order(client):
    create_task(client, "First")
    create_task(client, "Second")

    response = client.get("/api/tasks")

    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 2
    assert [t["title"] for t in data["tasks"]] == ["First", "Second"]


def test_filter_tasks_by_status(client):
    first = create_task(client, "Will start")
    create_task(client, "Stays pending")
    client.patch(f"/api/tasks/{first['id']}", json={"status": "in_progress"})

    in_progress = client.get("/api/tasks?status=in_progress").get_json()
    pending = client.get("/api/tasks?status=pending").get_json()

    assert in_progress["count"] == 1
    assert in_progress["tasks"][0]["title"] == "Will start"
    assert pending["count"] == 1
    assert pending["tasks"][0]["title"] == "Stays pending"


def test_filter_with_invalid_status_returns_400(client):
    response = client.get("/api/tasks?status=done")

    assert response.status_code == 400
    assert "Invalid status" in response.get_json()["error"]


# ---------- Retrieve one ----------

def test_get_task_success(client):
    created = create_task(client, "Find me", description="details")

    response = client.get(f"/api/tasks/{created['id']}")

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == created["id"]
    assert data["title"] == "Find me"
    assert data["description"] == "details"


def test_get_missing_task_returns_404(client):
    response = client.get("/api/tasks/999")

    assert response.status_code == 404
    assert "not found" in response.get_json()["error"]


def test_non_numeric_task_id_returns_json_404(client):
    response = client.get("/api/tasks/abc")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["error"] == "Resource not found"


# ---------- Update ----------

def test_update_task_status(client):
    created = create_task(client, "Change my status")

    response = client.patch(
        f"/api/tasks/{created['id']}", json={"status": "completed"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "completed"
    assert data["title"] == "Change my status"
    assert data["updated_at"].endswith("Z")


def test_update_title_and_clear_description(client):
    created = create_task(client, "Old title", description="Old description")

    response = client.patch(
        f"/api/tasks/{created['id']}",
        json={"title": "  New title  ", "description": None},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "New title"
    assert data["description"] is None


def test_update_with_invalid_status_returns_400_and_changes_nothing(client):
    created = create_task(client, "Keep me")

    response = client.patch(
        f"/api/tasks/{created['id']}",
        json={"title": "Should not apply", "status": "done"},
    )

    assert response.status_code == 400
    assert "Invalid status" in response.get_json()["error"]
    unchanged = client.get(f"/api/tasks/{created['id']}").get_json()
    assert unchanged["title"] == "Keep me"
    assert unchanged["status"] == "pending"


def test_update_with_unsupported_field_returns_400(client):
    created = create_task(client)

    response = client.patch(f"/api/tasks/{created['id']}", json={"titel": "typo"})

    assert response.status_code == 400
    assert "titel" in response.get_json()["error"]


def test_update_with_empty_body_returns_400(client):
    created = create_task(client)

    response = client.patch(f"/api/tasks/{created['id']}", json={})

    assert response.status_code == 400
    assert "at least one field" in response.get_json()["error"]


def test_update_with_blank_title_returns_400(client):
    created = create_task(client)

    response = client.patch(f"/api/tasks/{created['id']}", json={"title": "   "})

    assert response.status_code == 400
    assert "title" in response.get_json()["error"]


def test_update_with_malformed_json_returns_400(client):
    created = create_task(client)

    response = client.patch(
        f"/api/tasks/{created['id']}",
        data="not json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "JSON object" in response.get_json()["error"]


def test_update_missing_task_returns_404(client):
    response = client.patch("/api/tasks/999", json={"status": "completed"})

    assert response.status_code == 404
    assert "not found" in response.get_json()["error"]


# ---------- Delete ----------

def test_delete_task_success(client):
    created = create_task(client, "Delete me")

    response = client.delete(f"/api/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.get_json() == {
        "message": f"Task {created['id']} deleted",
        "id": created["id"],
    }
    assert client.get(f"/api/tasks/{created['id']}").status_code == 404


def test_delete_only_removes_the_requested_task(client):
    keep = create_task(client, "Keep")
    remove = create_task(client, "Remove")

    client.delete(f"/api/tasks/{remove['id']}")

    remaining = client.get("/api/tasks").get_json()
    assert remaining["count"] == 1
    assert remaining["tasks"][0]["id"] == keep["id"]


def test_delete_missing_task_returns_404(client):
    response = client.delete("/api/tasks/999")

    assert response.status_code == 404
    assert "not found" in response.get_json()["error"]


# ---------- Other error handling ----------

def test_create_task_with_malformed_json_returns_400(client):
    response = client.post(
        "/api/tasks", data="not json", content_type="application/json"
    )

    assert response.status_code == 400
    assert "JSON object" in response.get_json()["error"]


def test_wrong_http_method_returns_json_405(client):
    response = client.put("/api/tasks/1")

    assert response.status_code == 405
    assert response.get_json()["error"] == "Method not allowed for this URL"


def test_unexpected_error_returns_generic_json_500(app, client):
    # Add a route that deliberately crashes, to test our safety net.
    @app.get("/boom")
    def boom():
        raise RuntimeError("secret internal detail")

    response = client.get("/boom")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Internal server error"}
    assert "secret internal detail" not in response.get_data(as_text=True)