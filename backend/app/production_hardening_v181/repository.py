from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.production_hardening_v181 import ProductionHardeningRun

class ProductionHardeningRepository:
    @staticmethod
    async def create(*, session: AsyncSession, user_id: UUID, release_candidate: str, metadata: dict):
        row = ProductionHardeningRun(
            user_id=user_id,
            release_candidate=release_candidate,
            status="running",
            report={},
            run_metadata=metadata,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    @staticmethod
    async def get(*, session: AsyncSession, user_id: UUID, run_id: UUID):
        return await session.scalar(
            select(ProductionHardeningRun).where(
                ProductionHardeningRun.id == run_id,
                ProductionHardeningRun.user_id == user_id,
            )
        )

    @staticmethod
    async def save(*, session: AsyncSession, row: ProductionHardeningRun):
        await session.commit()
        await session.refresh(row)
        return row
