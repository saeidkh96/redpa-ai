from __future__ import annotations

import asyncio
from uuid import UUID

from app.research_agent.service import (
    ResearchAgentError,
    ResearchAgentService,
)
from app.research_workspace.quality import (
    ResearchQualityEvaluator,
)
from app.research_workspace.report import (
    EnterpriseResearchReportBuilder,
)
from app.research_workspace.repository import (
    EnterpriseResearchRepository,
)
from app.research_workspace.schemas import (
    EnterpriseResearchRequest,
    ResearchEvidenceItem,
)


class EnterpriseResearchService:
    @classmethod
    async def create(
        cls,
        payload: EnterpriseResearchRequest,
    ) -> UUID:
        return await EnterpriseResearchRepository.create_run(
            query=payload.query,
            max_results=payload.max_results,
            minimum_quality_score=payload.minimum_quality_score,
        )

    @classmethod
    async def execute(
        cls,
        run_id: UUID,
    ) -> None:
        run = await EnterpriseResearchRepository.get_run(
            run_id,
            include_timeline=False,
        )

        try:
            await cls._stage(
                run_id,
                "planning",
                10,
                "Planning evidence-first research execution.",
            )
            await asyncio.sleep(0)

            await cls._stage(
                run_id,
                "web_research",
                30,
                "Collecting and ranking web evidence.",
            )

            result = await ResearchAgentService.research(
                query=run.query,
                max_results=run.max_results,
            )

            evidence = [
                ResearchEvidenceItem(
                    title=item.title,
                    url=item.url,
                    snippet=item.snippet,
                    source_domain=item.source_domain,
                    score=item.score,
                )
                for item in result.evidence
            ]

            await EnterpriseResearchRepository.update_run(
                run_id,
                status="running",
                current_stage="synthesis",
                progress=65,
                provider=result.provider,
                evidence=[
                    item.model_dump(mode="json")
                    for item in evidence
                ],
            )
            await EnterpriseResearchRepository.add_event(
                run_id,
                stage="synthesis",
                status="running",
                message=(
                    f"Synthesizing {len(evidence)} ranked evidence items."
                ),
                metadata={
                    "evidence_count": len(evidence),
                    "provider": result.provider,
                },
            )

            quality = ResearchQualityEvaluator.evaluate(
                evidence,
                target_results=run.max_results,
                minimum_score=run.minimum_quality_score,
            )

            report = EnterpriseResearchReportBuilder.build(
                query=run.query,
                evidence=evidence,
                quality=quality,
            )

            await EnterpriseResearchRepository.add_event(
                run_id,
                stage="quality_gate",
                status=(
                    "completed"
                    if quality.passed
                    else "review"
                ),
                message=(
                    "Research quality gate passed."
                    if quality.passed
                    else "Research completed below the configured quality threshold."
                ),
                metadata=quality.model_dump(mode="json"),
            )

            await EnterpriseResearchRepository.update_run(
                run_id,
                status="completed",
                current_stage="completed",
                progress=100,
                provider=result.provider,
                report=report,
                evidence=[
                    item.model_dump(mode="json")
                    for item in evidence
                ],
                quality=quality.model_dump(mode="json"),
                completed=True,
            )
            await EnterpriseResearchRepository.add_event(
                run_id,
                stage="completed",
                status="completed",
                message="Enterprise research report is ready.",
            )

        except (
            ResearchAgentError,
            ValueError,
            RuntimeError,
        ) as exception:
            await EnterpriseResearchRepository.update_run(
                run_id,
                status="failed",
                current_stage="failed",
                progress=100,
                error=str(exception),
                completed=True,
            )
            await EnterpriseResearchRepository.add_event(
                run_id,
                stage="failed",
                status="failed",
                message=str(exception),
            )

    @staticmethod
    async def _stage(
        run_id: UUID,
        stage: str,
        progress: int,
        message: str,
    ) -> None:
        await EnterpriseResearchRepository.update_run(
            run_id,
            status="running",
            current_stage=stage,
            progress=progress,
        )
        await EnterpriseResearchRepository.add_event(
            run_id,
            stage=stage,
            status="running",
            message=message,
        )
