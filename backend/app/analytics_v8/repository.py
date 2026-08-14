from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import asyncpg

from app.analytics_v8.schemas import AnalyticsCatalog, AnalyticsEventCreate, KPIGroup, KPIQueryRequest, KPIQueryResponse


class AnalyticsRepository:
    @staticmethod
    def _database_url() -> str:
        value = os.getenv("DATABASE_URL", "").strip()
        if not value:
            raise RuntimeError("DATABASE_URL is required for analytics.")
        return value.replace("postgresql+asyncpg://", "postgresql://", 1)

    @classmethod
    async def _connect(cls) -> asyncpg.Connection:
        connection = await asyncpg.connect(cls._database_url(), timeout=15.0)
        await connection.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
        await connection.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
        return connection

    @classmethod
    async def insert_events(cls, items: list[AnalyticsEventCreate]) -> int:
        connection = await cls._connect()
        try:
            async with connection.transaction():
                for item in items:
                    await connection.execute(
                        """
                        INSERT INTO analytics_fact_events (
                            id, metric, value, weight, dimensions, metadata,
                            occurred_at, created_at
                        ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, NOW())
                        """,
                        uuid4(),
                        item.metric,
                        item.value,
                        item.weight,
                        item.dimensions,
                        item.metadata,
                        item.occurred_at or datetime.now(timezone.utc),
                    )
        finally:
            await connection.close()
        return len(items)

    @classmethod
    async def catalog(cls) -> AnalyticsCatalog:
        connection = await cls._connect()
        try:
            metrics = await connection.fetch("SELECT DISTINCT metric FROM analytics_fact_events ORDER BY metric")
            dimensions = await connection.fetch(
                """
                SELECT DISTINCT key
                FROM analytics_fact_events,
                     LATERAL jsonb_object_keys(dimensions) AS key
                ORDER BY key
                """
            )
        finally:
            await connection.close()
        return AnalyticsCatalog(
            metrics=[row["metric"] for row in metrics],
            dimensions=[row["key"] for row in dimensions],
        )

    @classmethod
    async def query(cls, payload: KPIQueryRequest) -> KPIQueryResponse:
        params: list[Any] = [payload.metric]
        where = ["metric = $1"]

        if payload.start_at is not None:
            params.append(payload.start_at)
            where.append(f"occurred_at >= ${len(params)}")
        if payload.end_at is not None:
            params.append(payload.end_at)
            where.append(f"occurred_at <= ${len(params)}")

        for key, value in payload.filters.items():
            params.extend([key, value])
            where.append(f"dimensions ->> ${len(params)-1} = ${len(params)}")

        dimension_selects: list[str] = []
        group_positions: list[str] = []
        dimension_keys: list[str] = []
        for key in payload.group_by:
            params.append(key)
            position = len(params)
            alias = f"d{len(dimension_selects)}"
            dimension_selects.append(f"dimensions ->> ${position} AS {alias}")
            group_positions.append(alias)
            dimension_keys.append(key)

        aggregation_sql = {
            "sum": "COALESCE(SUM(value), 0)",
            "avg": "COALESCE(AVG(value), 0)",
            "weighted_avg": "COALESCE(SUM(value * weight) / NULLIF(SUM(weight), 0), 0)",
            "count": "COUNT(*)::double precision",
            "min": "COALESCE(MIN(value), 0)",
            "max": "COALESCE(MAX(value), 0)",
        }[payload.aggregation]

        select_prefix = ", ".join(dimension_selects)
        if select_prefix:
            select_prefix += ", "
        group_clause = f"GROUP BY {', '.join(group_positions)}" if group_positions else ""
        order_clause = f"ORDER BY {', '.join(group_positions)}" if group_positions else ""

        sql = f"""
            SELECT {select_prefix}
                   {aggregation_sql} AS metric_value,
                   COUNT(*)::bigint AS event_count,
                   COALESCE(SUM(weight), 0)::double precision AS total_weight
            FROM analytics_fact_events
            WHERE {' AND '.join(where)}
            {group_clause}
            {order_clause}
        """

        connection = await cls._connect()
        try:
            rows = await connection.fetch(sql, *params)
        finally:
            await connection.close()

        groups: list[KPIGroup] = []
        for row in rows:
            dims = {key: (row[f"d{index}"] or "") for index, key in enumerate(dimension_keys)}
            groups.append(
                KPIGroup(
                    dimensions=dims,
                    value=float(row["metric_value"] or 0.0),
                    event_count=int(row["event_count"]),
                    total_weight=float(row["total_weight"] or 0.0),
                )
            )

        return KPIQueryResponse(
            metric=payload.metric,
            aggregation=payload.aggregation,
            groups=groups,
            total_groups=len(groups),
        )
