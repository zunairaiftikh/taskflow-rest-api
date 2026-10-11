HUGE_ID = 99999999999999999999  # larger than SQLite can store


def test_huge_task_id_returns_404(client):
    assert client.get(f"/api/tasks/{HUGE_ID}").status_code == 404
    assert client.patch(
        f"/api/tasks/{HUGE_ID}", json={"status": "completed"}
    ).status_code == 404
    assert client.delete(f"/api/tasks/{HUGE_ID}").status_code == 404


def test_create_task_with_too_long_title_returns_400(client):
    response = client.post("/api/tasks", json={"title": "x" * 201})

    assert response.status_code == 400
    assert "200" in response.get_json()["error"]


def test_create_task_with_non_string_description_returns_400(client):
    response = client.post("/api/tasks", json={"title": "ok", "description": 123})

    assert response.status_code == 400
    assert "description" in response.get_json()["error"]


def test_create_task_with_list_body_returns_400(client):
    response = client.post("/api/tasks", json=[1, 2, 3])

    assert response.status_code == 400
    assert "JSON object" in response.get_json()["error"]


def test_update_status_null_returns_400(client):
    created = client.post("/api/tasks", json={"title": "Keep status"}).get_json()

    response = client.patch(f"/api/tasks/{created['id']}", json={"status": None})

    assert response.status_code == 400
    assert "Invalid status" in response.get_json()["error"]


def test_update_with_too_long_title_returns_400(client):
    created = client.post("/api/tasks", json={"title": "Short"}).get_json()

    response = client.patch(
        f"/api/tasks/{created['id']}", json={"title": "x" * 201}
    )

    assert response.status_code == 400
    assert "200" in response.get_json()["error"]