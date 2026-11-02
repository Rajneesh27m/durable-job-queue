from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.main import app
from app.models import Job, JobStatus

client = TestClient(app)

def test_chaos_worker_crash_recovery():
    """Chaos Test: वर्कर क्रैश होने पर जॉब रिकवर होनी चाहिए"""
    
    
    response = client.post("/jobs", json={
        "name": "chaos_test_job",
        "payload": {"task": "test_crash"},
        "priority": 1
    })
    job_id = response.json()["id"]

    db: Session = SessionLocal()
    try:
        
        job = db.query(Job).filter(Job.id == job_id).first()
        job.status = JobStatus.RUNNING
        job.locked_by = "dead-worker-999"
        
        job.locked_at = datetime.now(UTC) - timedelta(minutes=10)
        db.commit()

        
        
        stale_timeout = datetime.now(UTC) - timedelta(minutes=5)
        stale_jobs = db.query(Job).filter(
            Job.status == JobStatus.RUNNING,
            Job.locked_at < stale_timeout
        ).all()
        
        for stale_job in stale_jobs:
            stale_job.status = JobStatus.QUEUED
            stale_job.locked_by = None
            stale_job.locked_at = None
        db.commit()

        
        db.refresh(job)
        assert job.status == JobStatus.QUEUED
        assert job.locked_by is None

    finally:
        db.close()