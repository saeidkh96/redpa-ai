from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: str


def _bool(value: Any) -> bool:
    return bool(value)


def validate(evidence: dict[str, Any]) -> list[CheckResult]:
    checks: list[CheckResult] = []

    stage6 = evidence.get("stage6", {})
    checks.append(CheckResult(
        "Stage 6 failure-path safety",
        _bool(stage6.get("recovery_failed_event"))
        and stage6.get("incident_status") == "failed"
        and stage6.get("run_status") == "failed"
        and not _bool(stage6.get("resolved_written")),
        "failed remediation must fail closed",
    ))

    stage7 = evidence.get("stage7", {})
    required_events = {
        "ops.remediation_blocked",
        "human.approval_granted",
        "run.resumed",
        "ops.remediation_started",
        "ops.recovery_verified",
        "run.completed",
    }
    actual_events = set(stage7.get("events", []))
    missing = sorted(required_events - actual_events)
    checks.append(CheckResult(
        "Stage 7 audit completeness",
        not missing,
        "missing=" + ",".join(missing) if missing else "complete",
    ))

    stage8 = evidence.get("stage8", {})
    checks.append(CheckResult(
        "Stage 8 idempotency",
        stage8.get("destructive_execution_count") == 1
        and _bool(stage8.get("duplicate_detected")),
        "duplicate requests must execute one destructive action",
    ))

    stage9 = evidence.get("stage9", {})
    checks.append(CheckResult(
        "Stage 9 persistence/restart recovery",
        _bool(stage9.get("incident_persisted"))
        and _bool(stage9.get("run_persisted"))
        and _bool(stage9.get("events_persisted"))
        and _bool(stage9.get("resumed_after_restart")),
        "state must survive process restart",
    ))

    first_four = all(c.passed for c in checks)
    checks.append(CheckResult(
        "Stage 10 readiness gate",
        first_four,
        "all Stage 6-9 checks must pass",
    ))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--evidence",
        default="artifacts/v11-production-validation-input.json",
        help="Path to collected Stage 6-9 evidence JSON",
    )
    parser.add_argument(
        "--output",
        default="artifacts/v11-production-validation.json",
        help="Path to generated validation report",
    )
    args = parser.parse_args()

    evidence_path = Path(args.evidence)
    if not evidence_path.exists():
        print(f"[ERROR] Evidence file not found: {evidence_path}")
        print("Copy docs/evidence-example.json to the expected location and replace placeholders.")
        return 2

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    checks = validate(evidence)
    overall = all(c.passed for c in checks)

    print("RedPA AI V11 Production Validation")
    print("=" * 36)
    for check in checks:
        state = "PASS" if check.passed else "FAIL"
        print(f"[{state}] {check.name} — {check.details}")

    report = {
        "version": "v11",
        "status": "PASS" if overall else "FAIL",
        "checks": [asdict(c) for c in checks],
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    print(f"PRODUCTION VALIDATION: {report['status']}")
    print(f"Evidence report: {output_path}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
