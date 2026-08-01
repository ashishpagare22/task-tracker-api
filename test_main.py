from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_task():
    response = client.post("/tasks", json={"title": "Write tests"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Write tests"
    assert data["completed"] == False
    assert "id" in data

def test_list_tasks():
    client.post("/tasks", json={"title": "Task A"})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_task_not_found():
    response = client.get("/tasks/9999")
    assert response.status_code == 404

def test_update_task():
    create = client.post("/tasks", json={"title": "Old title"})
    task_id = create.json()["id"]
    response = client.put(f"/tasks/{task_id}", json={"title": "New title", "completed": True})
    assert response.status_code == 200
    assert response.json()["completed"] == True

def test_delete_task():
    create = client.post("/tasks", json={"title": "Delete me"})
    task_id = create.json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404
