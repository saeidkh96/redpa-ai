from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.security.production_guard import (  # noqa: E402
    evaluate_production_configuration,
)


def main() -> int:
    findings = evaluate_production_configuration(
        dict(os.environ)
    )

    if findings:
        for finding in findings:
            print(
                f"[{finding.severity.upper()}] "
                f"{finding.code}: {finding.message}"
            )
        return 1

    print("[PASS] Production configuration baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
