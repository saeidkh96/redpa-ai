# Phase 17 — Event-driven Integrations / Messaging

Phase 17 adds:

- explicit event contracts;
- PostgreSQL transactional outbox;
- Redis Streams publication;
- retryable failed outbox rows;
- correlation and causation metadata;
- tenant-aware event metadata;
- authenticated Events API;
- Event & Integration Control Center.

## Why the outbox pattern?

Writing domain state and directly publishing to Redis in one application
operation can lose events when one side succeeds and the other fails.

The outbox gives RedPA a durable database record first. Publication to Redis
Streams happens separately and can be retried.
