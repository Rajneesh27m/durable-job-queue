from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    run_at: datetime | None = None
    idempotency_key: str | None = None

class JobResponse(BaseModel):
    id: UUID
    name: str
    payload: dict[str, Any]
    status: str
    priority: int
    attempts: int
    result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    status: str
    queued_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    dead_jobs: int