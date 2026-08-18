from __future__ import annotations

import json
import sys
from pathlib import Path

from app.self_healing.validation import validate


INPUT = Path(
    "artifacts/v12-self-healing-validation-input.json"
)

OUTPUT = Path(
    "artifacts/v12-self-healing-validation.json"
)


def main() -> int:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else INPUT
    )

    if not path.exists():
        print(
            f"[ERROR] Evidence file not found: {path}"
        )
        return 2

    evidence = json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )

    checks = validate(
        evidence
    )

    print(
        "RedPA AI V12 Self-Healing Validation"
    )
    print(
        "=" * 40
    )

    for check in checks:
        status = (
            "PASS"
            if check.passed
            else "FAIL"
        )

        print(
            f"[{status}] {check.name}"
        )

    passed = all(
        check.passed
        for check in checks
    )

    report = {
        "version": "12.0.0",
        "validation": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "checks": [
            {
                "name": check.name,
                "passed": check.passed,
            }
            for check in checks
        ],
    }

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()

    print(
        "SELF-HEALING VALIDATION: "
        f"{'PASS' if passed else 'FAIL'}"
    )

    print(
        f"Evidence report: {OUTPUT}"
    )

    return (
        0
        if passed
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )