# LIMITATIONS.md - System Failure Modes & Boundaries

While the durable job queue is designed to be resilient against worker crashes using PostgreSQL row-level locks (FOR UPDATE SKIP LOCKED), the system has inherent architectural limits and specific failure modes:

## 1. Single Point of Failure (SPOF)
* PostgreSQL Database: Since PostgreSQL is our only infrastructure component, any database-level failure (database engine crash, disk exhaustion, or network partition) renders both the API and worker fleet completely inoperable.

## 2. Table Bloat & Performance Degradation
* Unbounded Growth: Without an automated cleanup or vacuuming policy, a high volume of completed and dead jobs will cause index bloat and degrade polling query performance over time.
* Connection Limits: As the number of concurrent worker processes scales up, PostgreSQL can quickly exhaust its maximum connection pool (max_connections), leading to dropped connections and failed queries.

## 3. Worker Visibility & Lock Timeouts
* Coarse Lock Recovery: If a long-running job legitimately takes longer than the configured LOCK_TIMEOUT_SECONDS, the stale-recovery mechanism will falsely classify the worker as dead, mark the job back to QUEUED, and cause a second worker to execute it concurrently.
* Non-Preemptive Execution: If a worker process hangs in an un-interruptible I/O loop without crashing, it holds system resources until forcefully terminated externally.

## 4. Polling Overhead
* Resource Consumption: Polling the database at short fixed intervals introduces continuous read overhead on PostgreSQL even when the queue is completely empty.

## 5. Non-Idempotent Job Payloads
* At-Least-Once Delivery Risk: Because the system guarantees at-least-once processing in the event of mid-job worker crashes, any job author executing non-idempotent business logic (e.g., non-idempotent payments) risks partial duplicate execution unless idempotent keys are enforced end-to-end.