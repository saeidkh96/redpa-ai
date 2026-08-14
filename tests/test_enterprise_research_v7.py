from pathlib import Path

import httpx
import pytest

from app.research_workspace.quality import ResearchQualityEvaluator
from app.research_workspace.report import EnterpriseResearchReportBuilder
from app.research_workspace.schemas import (
    EnterpriseResearchRequest,
    ResearchEvidenceItem,
)
from redpa_sdk import RedPA, RedPAConfig


def _evidence(domain: str, index: int) -> ResearchEvidenceItem:
    return ResearchEvidenceItem(
        title=f"Source {index}",
        url=f"https://{domain}/article-{index}",
        snippet=f"Evidence item {index}",
        source_domain=domain,
        score=0.9,
    )


def test_v7_research_request_validation():
    request = EnterpriseResearchRequest(
        query="Compare enterprise agent platforms",
        max_results=8,
        minimum_quality_score=0.65,
    )
    assert request.max_results == 8
    assert request.minimum_quality_score == 0.65


def test_v7_quality_rewards_coverage_and_domain_diversity():
    evidence = [
        _evidence("one.example", 1),
        _evidence("two.example", 2),
        _evidence("three.example", 3),
        _evidence("four.example", 4),
    ]
    quality = ResearchQualityEvaluator.evaluate(
        evidence,
        target_results=4,
        minimum_score=0.80,
    )
    assert quality.coverage_score == 1.0
    assert quality.source_diversity_score == 1.0
    assert quality.score == 1.0
    assert quality.passed is True


def test_v7_report_preserves_evidence_provenance():
    evidence = [_evidence("source.example", 1)]
    quality = ResearchQualityEvaluator.evaluate(
        evidence,
        target_results=1,
        minimum_score=0.50,
    )
    report = EnterpriseResearchReportBuilder.build(
        query="What is RedPA?",
        evidence=evidence,
        quality=quality,
    )
    assert "https://source.example/article-1" in report
    assert "Retrieval score" in report
    assert "Provenance" in report


def test_v7_api_route_is_registered():
    router = Path("backend/app/api/v1/router.py").read_text(encoding="utf-8")
    api = Path("backend/app/api/v1/enterprise_research.py").read_text(encoding="utf-8")
    assert "enterprise_research_router" in router
    assert 'prefix="/research"' in api
    assert '"/runs"' in api
    assert '"/runs/{run_id}"' in api


def test_v7_migration_creates_research_run_and_event_tables():
    migration = Path(
        "backend/alembic/versions/v70a1b2c3d4e_enterprise_research_workspace.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "v70a1b2c3d4e"' in migration
    assert 'down_revision = "q55b4c5d6e7f"' in migration
    assert '"enterprise_research_runs"' in migration
    assert '"enterprise_research_events"' in migration


def test_v7_control_plane_route_and_navigation_exist():
    page = Path("frontend/app/control-plane/research/page.tsx")
    shell = Path("frontend/components/control-plane/ControlPlaneShell.tsx").read_text(
        encoding="utf-8"
    )
    assert page.exists()
    assert "/control-plane/research" in shell
    assert "Enterprise Research Workspace" in page.read_text(encoding="utf-8")


def test_v7_sdk_research_routes():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/api/v1/research/runs":
            return httpx.Response(200, json={"items": [], "total": 0})
        if request.method == "POST" and request.url.path == "/api/v1/research/runs":
            body = request.read()
            assert b"enterprise agent platform" in body
            return httpx.Response(
                202,
                json={
                    "id": "00000000-0000-0000-0000-000000000001",
                    "query": "enterprise agent platform",
                    "status": "queued",
                    "current_stage": "queued",
                    "progress": 0,
                    "max_results": 8,
                    "minimum_quality_score": 0.65,
                    "provider": None,
                    "report": None,
                    "evidence": [],
                    "quality": None,
                    "error": None,
                    "created_at": "2026-08-14T00:00:00Z",
                    "updated_at": "2026-08-14T00:00:00Z",
                    "completed_at": None,
                    "timeline": [],
                },
            )
        raise AssertionError(f"Unexpected route {request.method} {request.url.path}")

    with RedPA(
        RedPAConfig(base_url="http://redpa.test"),
        transport=httpx.MockTransport(handler),
    ) as client:
        assert client.research_runs()["total"] == 0
        started = client.start_research("enterprise agent platform")

    assert started["status"] == "queued"
