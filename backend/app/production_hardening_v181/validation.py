from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.production_hardening_v181.checks import (
    check_stage_1, check_stage_2, check_stage_3, check_stage_4, check_stage_5,
    check_stage_6, check_stage_7, check_stage_8, check_stage_9, check_stage_10,
)
from app.production_hardening_v181.schemas import HardeningStageResult, ReleaseHardeningReport

CHECKS = [
    ("V12-V18 integration", check_stage_1),
    ("Migration chain", check_stage_2),
    ("Authenticated API E2E", check_stage_3),
    ("Persistence and restart", check_stage_4),
    ("Failure injection", check_stage_5),
    ("Security boundaries", check_stage_6),
    ("Docker runtime", check_stage_7),
    ("Observability", check_stage_8),
    ("Release evidence", check_stage_9),
    ("Final regression gate", check_stage_10),
]

def validate_release_evidence(evidence: dict[str, Any], *, release_candidate: str = "v18.1.0-rc1") -> ReleaseHardeningReport:
    stages = []
    for idx, (name, fn) in enumerate(CHECKS, 1):
        passed, detail = fn(evidence)
        stages.append(HardeningStageResult(
            stage=idx,
            name=name,
            status="pass" if passed else "fail",
            detail=detail,
            evidence={},
        ))

    overall = "PASS" if all(stage.status == "pass" for stage in stages) else "FAIL"
    return ReleaseHardeningReport(
        release_candidate=release_candidate,
        overall_status=overall,
        stages=stages,
        generated_at=datetime.now(timezone.utc),
    )
