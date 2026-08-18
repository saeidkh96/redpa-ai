from __future__ import annotations

import json
import sys
from pathlib import Path

from app.adaptive_governance_v13.validation import validate_v13_evidence

INPUT = Path("artifacts/v13-adaptive-governance-validation-input.json")
OUTPUT = Path("artifacts/v13-adaptive-governance-validation.json")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT
    if not path.exists():
        print(f"[ERROR] Evidence file not found: {path}")
        return 2

    evidence = json.loads(path.read_text(encoding="utf-8-sig"))
    checks = validate_v13_evidence(evidence)

    print("RedPA AI V13 Adaptive Governance Validation")
    print("=" * 44)
    for check in checks:
        print(f"[{'PASS' if check.passed else 'FAIL'}] {check.name}")

    passed = all(check.passed for check in checks)
    report = {
        "version": "13.0.0",
        "validation": "PASS" if passed else "FAIL",
        "checks": [{"name": c.name, "passed": c.passed} for c in checks],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print()
    print(f"ADAPTIVE GOVERNANCE VALIDATION: {'PASS' if passed else 'FAIL'}")
    print(f"Evidence report: {OUTPUT}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
