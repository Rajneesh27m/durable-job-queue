from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_soak_queue_system():
    """Soak Test: 1000 जॉब्स लगातार भेजकर सिस्टम का लोड टेस्ट करना"""
    
    total_jobs = 1000
    
    
    for i in range(total_jobs):
        response = client.post("/jobs", json={
            "name": f"soak_job_{i}",
            "payload": {"task": "soak_load_test", "index": i},
            "priority": 1
        })
        assert response.status_code == 201  

    
    response = client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    
    
    total_in_system = data.get("queued_jobs", 0) + data.get("completed_jobs", 0) + data.get("running_jobs", 0)
    assert total_in_system >= total_jobs