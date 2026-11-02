import os
import random
import socket
import time
from datetime import UTC, datetime, timedelta

#from sqlalchemy import func
from app.database import SessionLocal
from app.models import Job, JobStatus

WORKER_ID = f"{socket.gethostname()}-{os.getpid()}"
LOCK_TIMEOUT_SECONDS = 60  

def recover_stale_jobs(db):
    """अगर कोई वर्कर काम करते हुए क्रैश हो जाए, तो उसकी जॉब्स को वापस QUEUED में डालना"""
    stale_time = datetime.now(UTC) - timedelta(seconds=LOCK_TIMEOUT_SECONDS)
    stale_jobs = db.query(Job).filter(
        Job.status == JobStatus.RUNNING,
        Job.locked_at < stale_time
    ).all()
    
    for job in stale_jobs:
        job.status = JobStatus.QUEUED
        job.locked_by = None
        job.locked_at = None
    
    if stale_jobs:
        db.commit()

def fetch_next_job(db):
    """FOR UPDATE SKIP LOCKED: यह सुनिश्चित करता है कि दो वर्कर एक ही जॉब न उठा लें"""
    now = datetime.now(UTC)
    job = (
        db.query(Job)
        .filter(
            Job.status == JobStatus.QUEUED,
            Job.run_at <= now
        )
        .order_by(Job.priority.desc(), Job.run_at.asc())
        .with_for_update(skip_locked=True)
        .first()
    )
    
    if job:
        job.status = JobStatus.RUNNING
        job.locked_by = WORKER_ID
        job.locked_at = now
        job.attempts += 1
        db.commit()
        db.refresh(job)
    return job

def execute_job(job):
    # Payload se task ka type nikalna (agar na ho toh "default" manna)
    task_type = job.payload.get("task", "default")
    
    # Flaky API Simulation
    if task_type == "flaky_api":
        # 70% chance hai ki API fail ho jayegi
        if random.random() < 0.7:
            raise Exception("Partner API 503 Service Unavailable or Timeout")
        return {"status": "success", "message": "Partner API worked this time!"}
        
    # Normal Tasks ke liye
    # Yahan slow tasks test karne ke liye time.sleep() bhi laga sakte hain
    return {"status": "success", "message": f"Task {task_type} completed"}

def run_worker():
    print(f"Worker {WORKER_ID} started and waiting for jobs...")
    while True:
        db = SessionLocal()
        try:
            recover_stale_jobs(db)
            job = fetch_next_job(db)
            
            if not job:
                time.sleep(1)  
                continue

            try:
                result = execute_job(job)
                job.status = JobStatus.COMPLETED
                job.result = result
            except Exception as e:
                
                if job.attempts < job.max_retries:
                    backoff_seconds = 2 ** job.attempts
                    job.run_at = datetime.now(UTC) + timedelta(seconds=backoff_seconds)
                    job.status = JobStatus.QUEUED
                    job.error_message = str(e)
                else:
                    job.status = JobStatus.DEAD  
                    job.error_message = f"Failed after {job.attempts} attempts. Error: {e!s}"
            finally:
                job.locked_by = None
                job.locked_at = None
                db.commit()

        except Exception:
            db.rollback()
            time.sleep(1)
        finally:
            db.close()

if __name__ == "__main__":
    run_worker()