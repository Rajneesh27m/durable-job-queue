import enum
import uuid

from sqlalchemy import JSON, Column, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    
    
    status: Column = Column (Enum(JobStatus), default=JobStatus.QUEUED, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    run_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    
    idempotency_key = Column(String(255), unique=True, nullable=True)
    
    
    attempts = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    
    locked_by = Column(String(100), nullable=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    
    
    result = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now())


Index("idx_jobs_fetch", Job.status, Job.run_at, Job.priority.desc())
Index("idx_jobs_idempotency", Job.idempotency_key)