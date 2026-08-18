from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adaptive_governance_v13.engine import adaptive_policy_engine
from app.models.platform_evolution import PlatformEvolutionRecord


class PlatformEvolutionService:
    async def _persist(
        self,
        *,
        session: AsyncSession,
        user_id,
        version: int,
        kind: str,
        status: str,
        summary: str,
        payload: dict[str, Any],
    ) -> PlatformEvolutionRecord:
        record = PlatformEvolutionRecord(
            user_id=user_id,
            version=version,
            kind=kind,
            status=status,
            summary=summary,
            payload=payload,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    async def list_records(self, *, session: AsyncSession, user_id, version: int | None):
        stmt = (
            select(PlatformEvolutionRecord)
            .where(PlatformEvolutionRecord.user_id == user_id)
            .order_by(PlatformEvolutionRecord.created_at.desc())
        )
        count_stmt = select(func.count()).select_from(PlatformEvolutionRecord).where(
            PlatformEvolutionRecord.user_id == user_id
        )
        if version is not None:
            stmt = stmt.where(PlatformEvolutionRecord.version == version)
            count_stmt = count_stmt.where(PlatformEvolutionRecord.version == version)
        items = list((await session.scalars(stmt.limit(100))).all())
        total = int((await session.scalar(count_stmt)) or 0)
        return items, total

    async def reliability(self, *, session, user_id, payload):
        if payload.health == "unhealthy" or payload.error_rate >= 0.20:
            action, status = "governed_remediation", "action_required"
        elif payload.health == "degraded" or payload.error_rate >= 0.05 or payload.latency_ms >= 1500:
            action, status = "investigate", "degraded"
        else:
            action, status = "observe", "healthy"
        return await self._persist(
            session=session,
            user_id=user_id,
            version=11,
            kind="closed_loop_reliability",
            status=status,
            summary=f"{payload.service}: {action}",
            payload={**payload.model_dump(), "recommended_action": action},
        )

    async def failover(self, *, session, user_id, payload):
        healthy = [a for a in payload.candidates if a not in set(payload.unhealthy_agents)]
        selected = healthy[0] if healthy else None
        return await self._persist(
            session=session,
            user_id=user_id,
            version=12,
            kind="agent_failover",
            status="routable" if selected else "blocked",
            summary=f"Selected {selected}" if selected else "No healthy agent candidate",
            payload={**payload.model_dump(), "selected_agent": selected},
        )

    async def adaptive_policy(self, *, session, user_id, payload):
        # Backwards-compatible V13 evolution endpoint.
        # The full V13 API persists runtime signals/proposals separately.
        class _Signal:
            def __init__(self, p):
                self.failure_rate = p.failure_rate
                self.error_rate = getattr(p, "error_rate", 0.0)
                self.incident_count = p.incident_count
                self.destructive = p.destructive
                self.write_access = getattr(p, "write_access", False)
                self.handles_secrets = getattr(p, "handles_secrets", False)
                self.external_network = getattr(p, "external_network", False)

        recommendation = adaptive_policy_engine.recommend(
            action=payload.action,
            signals=[_Signal(payload)],
        )
        return await self._persist(
            session=session,
            user_id=user_id,
            version=13,
            kind="policy_recommendation",
            status="recommendation",
            summary=(
                f"{payload.action}: recommend "
                f"{recommendation.recommended_decision}/"
                f"{recommendation.recommended_risk}"
            ),
            payload={
                **payload.model_dump(),
                **recommendation.model_dump(),
                "auto_applied": False,
            },
        )

    async def compliance(self, *, session, user_id, payload):
        missing = [key for key in payload.required_fields if key not in payload.evidence]
        return await self._persist(
            session=session,
            user_id=user_id,
            version=14,
            kind="compliance_evidence",
            status="complete" if not missing else "incomplete",
            summary=f"{payload.control}: {'complete' if not missing else 'missing evidence'}",
            payload={**payload.model_dump(), "missing_fields": missing},
        )

    async def cloud_readiness(self, *, session, user_id, payload):
        checks = {
            "health_checks": payload.health_checks,
            "backups": payload.backups,
            "secrets_manager": payload.secrets_manager,
            "autoscaling": payload.autoscaling,
            "telemetry": payload.telemetry,
        }
        score = sum(bool(v) for v in checks.values()) / len(checks)
        return await self._persist(
            session=session,
            user_id=user_id,
            version=15,
            kind="cloud_readiness",
            status="ready" if score >= 0.8 else "not_ready",
            summary=f"{payload.environment}: readiness {score:.0%}",
            payload={**payload.model_dump(), "readiness_score": score},
        )

    async def rollout(self, *, session, user_id, payload):
        score_delta = payload.candidate_score - payload.baseline_score
        promote = score_delta >= 0.02 and payload.error_rate_delta <= 0.01
        decision = "PROMOTE" if promote else "HOLD"
        return await self._persist(
            session=session,
            user_id=user_id,
            version=16,
            kind="continuous_evaluation",
            status=decision.lower(),
            summary=f"{payload.candidate}: {decision}",
            payload={**payload.model_dump(), "score_delta": score_delta, "decision": decision},
        )

    async def connector(self, *, session, user_id, payload):
        risk_points = int(payload.write_access) + int(payload.external_network) + int(payload.handles_secrets)
        approval = payload.approval_required or risk_points >= 2
        risk = "HIGH" if risk_points >= 2 else ("MEDIUM" if risk_points == 1 else "LOW")
        return await self._persist(
            session=session,
            user_id=user_id,
            version=17,
            kind="connector_assessment",
            status="review" if approval else "allowed",
            summary=f"{payload.connector}: {risk}",
            payload={**payload.model_dump(), "risk": risk, "effective_approval_required": approval},
        )

    async def register_agent(self, *, session, user_id, payload):
        trusted = payload.signed_manifest and payload.health_endpoint and payload.governance_compatible
        return await self._persist(
            session=session,
            user_id=user_id,
            version=18,
            kind="agent_registry",
            status="trusted" if trusted else "restricted",
            summary=f"{payload.agent_id}@{payload.version}: {'trusted' if trusted else 'restricted'}",
            payload={**payload.model_dump(), "trust_state": "trusted" if trusted else "restricted"},
        )


platform_evolution_service = PlatformEvolutionService()
