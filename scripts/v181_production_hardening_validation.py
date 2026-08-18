from __future__ import annotations

import json
import sys
from pathlib import Path

from app.production_hardening_v181.validation import validate_release_evidence

INPUT = Path("artifacts/v181-production-hardening-input.json")
OUTPUT = Path("artifacts/v181-production-hardening.json")

def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT
    if not path.exists():
        print(f"[ERROR] Evidence file not found: {path}")
        return 2

    evidence = json.loads(path.read_text(encoding="utf-8-sig"))
    report = validate_release_evidence(evidence)

    print("RedPA AI V18.1 Production Hardening")
    print("=" * 40)
    for stage in report.stages:
        print(f"[{stage.status.upper()}] Stage {stage.stage} {stage.name} — {stage.detail}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    print()
    print(f"PRODUCTION HARDENING: {report.overall_status}")
    print(f"Evidence report: {OUTPUT}")
    return 0 if report.overall_status == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
