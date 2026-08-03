from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True, slots=True)
class CheckResult:
    name: str
    success: bool
    detail: str


def run_command(
    name: str,
    command: list[str],
) -> CheckResult:
    process = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = (
        process.stdout.strip()
        or process.stderr.strip()
        or "No output."
    )

    return CheckResult(
        name=name,
        success=process.returncode == 0,
        detail=output[-4000:],
    )


def check_required_paths() -> CheckResult:
    required = [
        "backend/app/main.py",
        "backend/app/api/v1/router.py",
        "backend/app/monitoring/metrics.py",
        "backend/app/agent_memory",
        "backend/app/background_jobs",
        "backend/app/observability",
        "backend/app/performance",
        "backend/app/health",
        "docker-compose.yml",
        "Dockerfile",
        "requirements.txt",
        "README.md",
        "LICENSE",
    ]

    missing = [
        path
        for path in required
        if not (
            ROOT / path
        ).exists()
    ]

    return CheckResult(
        name="required_paths",
        success=not missing,
        detail=(
            "All required paths exist."
            if not missing
            else "Missing: "
            + ", ".join(missing)
        ),
    )


def check_debug_files() -> CheckResult:
    suspicious_names = {
        "test.txt",
        "debug.txt",
        "temp.txt",
        "tmp.txt",
        "output.txt",
    }

    matches = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if any(
            part in {
                ".git",
                ".venv",
                "__pycache__",
                ".pytest_cache",
            }
            for part in path.parts
        ):
            continue

        if path.name.casefold() in suspicious_names:
            matches.append(
                str(
                    path.relative_to(ROOT)
                )
            )

    return CheckResult(
        name="debug_files",
        success=not matches,
        detail=(
            "No suspicious temporary files found."
            if not matches
            else "Review: "
            + ", ".join(matches)
        ),
    )


def main() -> None:
    checks = [
        check_required_paths(),
        check_debug_files(),
        run_command(
            "compileall",
            [
                sys.executable,
                "-m",
                "compileall",
                "backend/app",
            ],
        ),
        run_command(
            "pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "tests",
                "-q",
            ],
        ),
        run_command(
            "docker_compose_config",
            [
                "docker",
                "compose",
                "config",
            ],
        ),
    ]

    report = {
        "release": "v1.0.0",
        "success": all(
            check.success
            for check in checks
        ),
        "checks": [
            {
                "name": check.name,
                "success": check.success,
                "detail": check.detail,
            }
            for check in checks
        ],
    }

    output_path = (
        ROOT
        / "release-check-report.json"
    )

    output_path.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    for check in checks:
        status = (
            "PASS"
            if check.success
            else "FAIL"
        )

        print(
            f"[{status}] {check.name}"
        )

    print(
        f"\nReport: {output_path}"
    )

    if not report["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
