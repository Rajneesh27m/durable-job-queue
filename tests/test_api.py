from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_create_job():
    """चेक करें कि क्या नई जॉब सही से बन रही है"""
    response = client.post("/jobs", json={
        "name": "email_job",
        "payload": {"to": "test@example.com"},
        "priority": 1
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "queued"
    assert data["name"] == "email_job"

def test_get_stats():
    """चेक करें कि क्या स्टैट्स API सही रिस्पॉन्स दे रही है"""
    response = client.get("/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "queued_jobs" in data
    assert "completed_jobs" in data
    assert "status" in data