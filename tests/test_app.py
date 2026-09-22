from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_chat_requires_consent():
    response = client.post(
        "/api/chat",
        json={
            "conversation_id": "test-conversation",
            "message": "hello",
            "consent": False,
        },
    )
    assert response.status_code == 400
