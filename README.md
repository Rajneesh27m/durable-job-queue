# Durable Job Queue

A resilient, production-ready distributed background job queue system engineered strictly using PostgreSQL as the sole infrastructure layer—with zero external queue dependencies (no Redis, Celery, RQ, or Kafka). 

Built with FastAPI, SQLAlchemy 2, and Docker Compose, this system guarantees reliable job processing, concurrency control, and automatic fault recovery under worker failures.

---

## Architecture & Guarantees

* Postgres-Only Infrastructure: Leverages PostgreSQL's row-level locking mechanisms via FOR UPDATE SKIP LOCKED. Multiple worker instances poll and claim pending jobs simultaneously without race conditions or database deadlocks.
* At-Least-Once Delivery: Jobs are guaranteed never to be lost. Every claimed job is guarded by a heartbeat/lock timestamp.
* Mid-Job Crash Resilience (Chaos Recovery): If a worker terminates or dies mid-execution, a stale-recovery process identifies the expired lock timeout, resets the job state to QUEUED, and allows an available worker to resume execution.
* Idempotency Protection: Clients submitting requests with an idempotency_key will never trigger duplicate job instances, protecting against duplicate network retries.
* Exponential Backoff & Dead Letter Handling: Jobs failing execution are retried sensibly with incremental backoff. Jobs that permanently exceed retry thresholds are transitioned to the DEAD state for operator inspection.

---

## Tech Stack

* Language: Python 3.11
* API Framework: FastAPI, Uvicorn
* Database & ORM: PostgreSQL 15, SQLAlchemy 2, Alembic
* Containerization: Docker, Docker Compose
* Validation & Code Quality: pytest, ruff, mypy

---

## Project Structure

`text
durable-job-queue/
├── app/
│   ├── database.py       # Engine & session connection management
│   ├── models.py         # SQLAlchemy models (Jobs table & state enums)
│   ├── schemas.py        # Pydantic input/output validation schemas
│   ├── main.py           # FastAPI endpoints
│   └── worker.py         # Consumer polling loop & crash recovery
├── tests/
│   ├── test_api.py       # API contract tests
│   ├── test_chaos.py     # Worker kill & stale-recovery validation
│   └── test_soak.py      # High-throughput load testing
├── docker-compose.yml    # Multi-container orchestration (db, web, worker)
├── Dockerfile            # Container build recipe
├── DESIGN.md             # System trade-offs, assumptions & architecture
├── LIMITATIONS.md        # Identified failure modes & boundary conditions
└── README.md