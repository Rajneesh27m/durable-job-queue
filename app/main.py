from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Job, JobStatus
from app.schemas import JobCreate, JobResponse, StatsResponse

app = FastAPI(title="Durable Job Queue API")


@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)


@app.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    
    if job_in.idempotency_key:
        existing = db.query(Job).filter(Job.idempotency_key == job_in.idempotency_key).first()
        if existing:
            return existing

    new_job = Job(
        name=job_in.name,
        payload=job_in.payload,
        priority=job_in.priority,
        run_at=job_in.run_at if job_in.run_at else func.now(),
        idempotency_key=job_in.idempotency_key
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


@app.get("/jobs/{id}", response_model=JobResponse)
def get_job(id: UUID, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    counts: list  = db.query(Job.status, func.count(Job.id)).group_by(Job.status).all()
    status_map = {s.value: 0 for s in JobStatus}
    
    for st, count in counts:
        status_map[st.value] = count

    return StatsResponse(
        status="healthy",
        queued_jobs=status_map[JobStatus.QUEUED.value],
        running_jobs=status_map[JobStatus.RUNNING.value],
        completed_jobs=status_map[JobStatus.COMPLETED.value],
        failed_jobs=status_map[JobStatus.FAILED.value],
        dead_jobs=status_map[JobStatus.DEAD.value],
    )