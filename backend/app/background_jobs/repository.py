from __future__ import annotations
import json
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import asyncpg
from app.background_jobs.schemas import BackgroundJobCreate, BackgroundJobRecord

class BackgroundJobNotFoundError(LookupError):
    pass

class BackgroundJobRepository:
    @staticmethod
    def _url() -> str:
        value = os.getenv("DATABASE_URL", "")
        return value.replace("postgresql+asyncpg://", "postgresql://", 1)

    @classmethod
    async def _connect(cls):
        connection = await asyncpg.connect(cls._url())
        await connection.set_type_codec(
            "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )
        return connection

    @classmethod
    async def ensure_schema(cls):
        c = await cls._connect()
        try:
            await c.execute('''
                CREATE TABLE IF NOT EXISTS background_jobs (
                    id UUID PRIMARY KEY,
                    job_type VARCHAR(100) NOT NULL,
                    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                    status VARCHAR(32) NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    available_at TIMESTAMPTZ NOT NULL,
                    locked_at TIMESTAMPTZ NULL,
                    completed_at TIMESTAMPTZ NULL,
                    failed_at TIMESTAMPTZ NULL,
                    last_error TEXT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
            ''')
        finally:
            await c.close()

    @classmethod
    async def enqueue(cls, payload: BackgroundJobCreate):
        await cls.ensure_schema()
        now = datetime.now(timezone.utc)
        c = await cls._connect()
        try:
            row = await c.fetchrow('''
                INSERT INTO background_jobs
                (id, job_type, payload, status, attempt_count, max_attempts,
                 available_at, created_at, updated_at)
                VALUES ($1, $2, $3::jsonb, 'queued', 0, $4, $5, $6, $6)
                RETURNING *
            ''', uuid4(), payload.job_type, payload.payload, payload.max_attempts,
                 now + timedelta(seconds=payload.delay_seconds), now)
        finally:
            await c.close()
        return cls._record(row)

    @classmethod
    async def claim_next(cls):
        await cls.ensure_schema()
        c = await cls._connect()
        try:
            async with c.transaction():
                row = await c.fetchrow('''
                    SELECT * FROM background_jobs
                    WHERE status='queued' AND available_at <= NOW()
                    ORDER BY available_at, created_at
                    FOR UPDATE SKIP LOCKED LIMIT 1
                ''')
                if row is None:
                    return None
                row = await c.fetchrow('''
                    UPDATE background_jobs
                    SET status='running',
                        attempt_count=attempt_count+1,
                        locked_at=NOW(),
                        updated_at=NOW()
                    WHERE id=$1 RETURNING *
                ''', row["id"])
        finally:
            await c.close()
        return cls._record(row)

    @classmethod
    async def complete(cls, job_id: UUID):
        c = await cls._connect()
        try:
            await c.execute('''
                UPDATE background_jobs
                SET status='completed', completed_at=NOW(),
                    locked_at=NULL, updated_at=NOW()
                WHERE id=$1
            ''', job_id)
        finally:
            await c.close()

    @classmethod
    async def fail(cls, job, error: str):
        c = await cls._connect()
        try:
            if job.attempt_count >= job.max_attempts:
                await c.execute('''
                    UPDATE background_jobs
                    SET status='dead_letter', failed_at=NOW(),
                        locked_at=NULL, last_error=$2, updated_at=NOW()
                    WHERE id=$1
                ''', job.id, error)
            else:
                delay = min(2 ** job.attempt_count * 10, 3600)
                await c.execute('''
                    UPDATE background_jobs
                    SET status='queued',
                        available_at=NOW()+make_interval(secs=>$2),
                        locked_at=NULL, last_error=$3, updated_at=NOW()
                    WHERE id=$1
                ''', job.id, delay, error)
        finally:
            await c.close()

    @classmethod
    async def list(cls, status: str | None = None, limit: int = 100):
        await cls.ensure_schema()
        c = await cls._connect()
        try:
            rows = await c.fetch('''
                SELECT * FROM background_jobs
                WHERE ($1::varchar IS NULL OR status=$1)
                ORDER BY created_at DESC LIMIT $2
            ''', status, limit)
        finally:
            await c.close()
        return [cls._record(row) for row in rows]

    @staticmethod
    def _record(row):
        payload = row["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        return BackgroundJobRecord(
            id=row["id"], job_type=row["job_type"], payload=payload,
            status=row["status"], attempt_count=row["attempt_count"],
            max_attempts=row["max_attempts"], available_at=row["available_at"],
            locked_at=row["locked_at"], completed_at=row["completed_at"],
            failed_at=row["failed_at"], last_error=row["last_error"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )
