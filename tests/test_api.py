import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_task_endpoint_invalid_secret():
    payload = {
        "email": "test@example.com",
        "secret": "wrong_secret",
        "task": "test-task",
        "round": 1,
        "nonce": "test-nonce",
        "brief": "Create a simple app",
        "evaluation_url": "https://example.com/eval"
    }
    
    response = client.post("/task", json=payload)
    assert response.status_code == 401


def test_task_endpoint_valid_secret(mocker):
    # Mock the background task
    mocker.patch("app.main.process_task")
    
    payload = {
        "email": "test@example.com",
        "secret": settings.secret_key,
        "task": "test-task",
        "round": 1,
        "nonce": "test-nonce",
        "brief": "Create a simple app",
        "evaluation_url": "https://example.com/eval"
    }
    
    response = client.post("/task", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"