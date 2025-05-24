import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DB = "./test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply override
app.dependency_overrides[get_db] = override_get_db

# Create schema
Base.metadata.create_all(bind=engine)

# Test client
client = TestClient(app)

# Test fixtures
@pytest.fixture(scope="module")
def user_tokens():
    u1 = {"username": "user1", "email": "user1@test.com", "password": "password"}
    u2 = {"username": "user2", "email": "user2@test.com", "password": "password"}

    for u in [u1, u2]:
        client.post("/api/auth/register", json=u)

    r1 = client.post("/api/auth/login", data={"username": u1["username"], "password": u1["password"]})
    r2 = client.post("/api/auth/login", data={"username": u2["username"], "password": u2["password"]})

    return {
        "user1": {
            "access": r1.json()["access_token"],
            "refresh": r1.json()["refresh_token"],
        },
        "user2": {
            "access": r2.json()["access_token"],
            "refresh": r2.json()["refresh_token"],
        },
    }

def test_refresh_token(user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens['user1']['refresh']}"}
    response = client.post("/api/auth/refresh", headers=headers)
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_logout(user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens['user2']['refresh']}"}
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200

def test_create_event(user_tokens):
    event = {
        "title": "Test Event",
        "description": "Create new Profile Test Event",
        "start_time": "2025-05-24",
        "end_time": "2025-05-24",
        "location": "Remote",
        "is_recurring": "false",
        "recurrence_pattern": "string"
    }
    headers = {"Authorization": f"Bearer {user_tokens['user1']['access']}"}
    response = client.post("/api/events", json=event, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Event"

def test_list_events(user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens['user1']['access']}"}
    response = client.get("/api/events", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_event(user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens['user1']['access']}"}
    response = client.get("/api/events/1", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == 1

def test_update_event(user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens['user1']['access']}"}
    update = {
        "title": "Updated Event",
        "description": "Create new Profile Test Event",
        "start_time": "2025-05-24",
        "end_time": "2025-05-24",
        "location": "Remote",
        "is_recurring": "false",
        "recurrence_pattern": "string"
    }
    response = client.put("/api/events/1", json=update, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Event"

def test_delete_event(user_tokens):
    headers = {"Authorization": f"Bearer {user_tokens['user1']['access']}"}
    response = client.delete("/api/events/1", headers=headers)
    assert response.status_code == 200

@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
