import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_and_teardown():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def get_auth_token(email="user@example.com", password="testpass123"):
    client.post("/signup", json={"email": email, "password": password})
    response = client.post("/login", data={"username": email, "password": password})
    return response.json()["access_token"]

def auth_headers(email="user@example.com", password="testpass123"):
    token = get_auth_token(email=email, password=password)
    return {"Authorization": f"Bearer {token}"}

def test_signup():
    response = client.post("/signup", json={"email": "new@example.com", "password": "pass123"})
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"

def test_signup_duplicate_email():
    client.post("/signup", json={"email": "dup@example.com", "password": "pass123"})
    response = client.post("/signup", json={"email": "dup@example.com", "password": "pass123"})
    assert response.status_code == 400

def test_login_success():
    client.post("/signup", json={"email": "login@example.com", "password": "pass123"})
    response = client.post("/login", data={"username": "login@example.com", "password": "pass123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password():
    client.post("/signup", json={"email": "wrong@example.com", "password": "pass123"})
    response = client.post("/login", data={"username": "wrong@example.com", "password": "wrongpass"})
    assert response.status_code == 401

def test_create_task_requires_auth():
    response = client.post("/tasks", json={"title": "No auth"})
    assert response.status_code == 401

def test_create_task_with_auth():
    response = client.post("/tasks", json={"title": "Write tests"}, headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Write tests"

def test_list_tasks():
    headers = auth_headers()
    client.post("/tasks", json={"title": "Task A"}, headers=headers)
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_task_not_found():
    response = client.get("/tasks/9999", headers=auth_headers())
    assert response.status_code == 404

def test_update_task():
    headers = auth_headers()
    create = client.post("/tasks", json={"title": "Old title"}, headers=headers)
    task_id = create.json()["id"]
    response = client.put(f"/tasks/{task_id}", json={"title": "New title", "completed": True}, headers=headers)
    assert response.status_code == 200
    assert response.json()["completed"] == True

def test_delete_task():
    headers = auth_headers()
    create = client.post("/tasks", json={"title": "Delete me"}, headers=headers)
    task_id = create.json()["id"]
    response = client.delete(f"/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    get_response = client.get(f"/tasks/{task_id}", headers=headers)
    assert get_response.status_code == 404

def test_users_cannot_see_each_others_tasks():
    headers_a = auth_headers(email="usera@example.com")
    headers_b = auth_headers(email="userb@example.com")
    create = client.post("/tasks", json={"title": "User A's task"}, headers=headers_a)
    task_id = create.json()["id"]
    response = client.get(f"/tasks/{task_id}", headers=headers_b)
    assert response.status_code == 404
