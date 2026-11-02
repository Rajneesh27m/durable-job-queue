# DESIGN.md - Durable Job Queue

## 1. Assumptions
* Infrastructure Restriction: As per the requirements, PostgreSQL is the only permitted infrastructure. Tools like Celery, Redis, RQ, or Kafka are strictly prohibited.
* Worker Volatility: Workers can crash, die, or be terminated at any moment, even mid-job.
* Idempotency: If a client retries a submission, it should not create duplicate jobs. We assume the client will provide a unique idempotency_key to ensure this.
* Job Execution Time: Jobs are expected to complete within a reasonable timeframe. We have established a 'Lock Timeout' mechanism so that if a worker crashes mid-job, the system can identify the stalled job and return it to the queue for retry.

## 2. Open Questions for the Client
* Job Retention: Should we keep successfully completed jobs in the database indefinitely, or should we implement a purge mechanism to delete them after a certain period?
* Peak Load: What is the maximum expected throughput (jobs per second)? This information is crucial for properly tuning the database connection pool.
* Maximum Job Duration: What is the longest acceptable execution time for any single job? Knowing this will help us configure accurate and reliable timeouts for the workers.

## 3. Alternatives Rejected
* Celery / RabbitMQ / Kafka: These standard job queue tools were immediately rejected to adhere strictly to the "Postgres only" infrastructure constraint.
* Standard Polling without Locks: We rejected using a basic SELECT ... WHERE status='QUEUED' query. In a multi-worker environment, this would lead to race conditions where multiple workers might fetch and execute the exact same job simultaneously.
* Selected Approach: To prevent race conditions, we utilize PostgreSQL's row-level locks, specifically the FOR UPDATE SKIP LOCKED clause. This ensures that multiple workers can pull jobs concurrently without overlapping or locking the entire table.