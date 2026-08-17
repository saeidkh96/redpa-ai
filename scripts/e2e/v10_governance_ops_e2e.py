from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid

import httpx

BASE = os.getenv(
    "REDPA_BASE_URL",
    "http://localhost:8000",
)
CONTAINER = os.getenv(
    "REDPA_E2E_CONTAINER",
    "redpa-research-agent",
)
PASSWORD = os.getenv(
    "REDPA_E2E_PASSWORD",
    "V10E2ETest123",
)


def docker(*args: str) -> str:
    result = subprocess.run(
        ["docker", *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def require_success(
    response: httpx.Response,
    *,
    stage: str,
) -> httpx.Response:
    if response.status_code >= 400:
        raise RuntimeError(
            f"{stage} failed: "
            f"{response.status_code} "
            f"{response.text}"
        )
    return response


def wait_for_health(
    client: httpx.Client,
    timeout: int = 90,
) -> None:
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            response = client.get(
                f"{BASE}/api/v1/health"
            )

            if response.status_code == 200:
                payload = response.json()

                if payload.get("status") == "healthy":
                    return

        except (
            httpx.HTTPError,
            ValueError,
        ):
            pass

        time.sleep(2)

    raise RuntimeError(
        "RedPA backend did not become healthy."
    )


def main() -> int:
    email = (
        f"v10-e2e-"
        f"{uuid.uuid4().hex[:10]}"
        f"@example.com"
    )

    with httpx.Client(
        timeout=30,
    ) as client:
        wait_for_health(client)

        register = client.post(
            f"{BASE}/api/v1/users/register",
            json={
                "email": email,
                "full_name": "V10 E2E",
                "password": PASSWORD,
            },
        )

        require_success(
            register,
            stage="User registration",
        )

        login = client.post(
            f"{BASE}/api/v1/auth/login",
            data={
                "username": email,
                "password": PASSWORD,
            },
        )

        require_success(
            login,
            stage="Authentication",
        )

        login_payload = login.json()

        token = login_payload.get(
            "access_token"
        )

        if not token:
            raise RuntimeError(
                "Authentication response did not "
                "contain access_token."
            )

        headers = {
            "Authorization": f"Bearer {token}"
        }

        incident = client.post(
            (
                f"{BASE}/api/v1/"
                "operations/v9/incidents"
            ),
            json={
                "service": CONTAINER,
                "summary": (
                    "Automated V10.3 governed "
                    "recovery E2E"
                ),
                "severity": "warning",
                "source": "v10.3-e2e",
                "metadata": {
                    "automated": True,
                },
            },
        )

        require_success(
            incident,
            stage="Incident creation",
        )

        incident_id = incident.json()["id"]

        run = client.post(
            (
                f"{BASE}/api/v1/"
                f"operations/v9/incidents/"
                f"{incident_id}/governance-run"
            ),
            headers=headers,
        )

        require_success(
            run,
            stage="Governance run creation",
        )

        run_id = run.json()["id"]

        try:
            docker(
                "stop",
                CONTAINER,
            )

            state = docker(
                "inspect",
                CONTAINER,
                "--format",
                "{{.State.Status}}",
            )

            if state != "exited":
                raise RuntimeError(
                    f"Expected container to be "
                    f"exited, got {state}."
                )

            diagnosis = client.post(
                (
                    f"{BASE}/api/v1/"
                    f"operations/v9/incidents/"
                    f"{incident_id}/governed/"
                    f"{run_id}/diagnose"
                ),
                headers=headers,
            )

            require_success(
                diagnosis,
                stage="Governed diagnosis",
            )

            diagnosis_payload = (
                diagnosis.json()
            )

            diagnosis_data = (
                diagnosis_payload[
                    "diagnosis"
                ]
            )

            assert (
                diagnosis_data["state"]
                == "exited"
            )

            assert (
                diagnosis_data[
                    "recommendation"
                ]
                == "restart_container"
            )

            denied = client.post(
                (
                    f"{BASE}/api/v1/"
                    f"operations/v9/incidents/"
                    f"{incident_id}/governed/"
                    f"{run_id}/remediate"
                ),
                headers=headers,
                json={
                    "action": (
                        "restart_container"
                    ),
                    "reason": (
                        "Automated V10.3 "
                        "denial path validation"
                    ),
                    "approved": False,
                },
            )

            require_success(
                denied,
                stage=(
                    "Denied remediation"
                ),
            )

            denied_payload = denied.json()

            assert (
                denied_payload["status"]
                == "denied"
            )

            state = docker(
                "inspect",
                CONTAINER,
                "--format",
                "{{.State.Status}}",
            )

            assert state == "exited"

            blocked = client.get(
                (
                    f"{BASE}/api/v1/"
                    f"governance/v10/runs/"
                    f"{run_id}"
                ),
                headers=headers,
            )

            require_success(
                blocked,
                stage="Blocked run check",
            )

            blocked_payload = (
                blocked.json()
            )

            assert (
                blocked_payload["status"]
                == "blocked"
            )

            approved = client.post(
                (
                    f"{BASE}/api/v1/"
                    f"operations/v9/incidents/"
                    f"{incident_id}/governed/"
                    f"{run_id}/remediate"
                ),
                headers=headers,
                json={
                    "action": (
                        "restart_container"
                    ),
                    "reason": (
                        "Automated V10.3 "
                        "approved recovery "
                        "validation"
                    ),
                    "approved": True,
                },
            )

            require_success(
                approved,
                stage=(
                    "Approved remediation"
                ),
            )

            approved_payload = (
                approved.json()
            )

            assert (
                approved_payload["status"]
                == "completed"
            )

            state = docker(
                "inspect",
                CONTAINER,
                "--format",
                "{{.State.Status}}",
            )

            assert state == "running"

            final = client.get(
                (
                    f"{BASE}/api/v1/"
                    f"governance/v10/runs/"
                    f"{run_id}"
                ),
                headers=headers,
            )

            require_success(
                final,
                stage="Final run check",
            )

            payload = final.json()

            events = [
                item["event_type"]
                for item
                in payload["events"]
            ]

            assert (
                payload["status"]
                == "completed"
            )

            assert (
                payload[
                    "evaluation_run_id"
                ]
            )

            assert (
                payload[
                    "evaluation_score"
                ]
                is not None
            )

            required_events = [
                "policy.decision",
                "ops.remediation_blocked",
                "run.running",
                "ops.remediation_started",
                "ops.recovery_verified",
                "run.completed",
                "evaluation.completed",
            ]

            for required in required_events:
                assert required in events

            print(
                json.dumps(
                    {
                        "result": "PASS",
                        "incident_id": (
                            incident_id
                        ),
                        "run_id": run_id,
                        "status": (
                            payload["status"]
                        ),
                        "evaluation_score": (
                            payload[
                                "evaluation_score"
                            ]
                        ),
                        "container": docker(
                            "inspect",
                            CONTAINER,
                            "--format",
                            "{{.State.Status}}",
                        ),
                        "events": events,
                    },
                    indent=2,
                )
            )

            return 0

        finally:
            try:
                state = docker(
                    "inspect",
                    CONTAINER,
                    "--format",
                    "{{.State.Status}}",
                )

                if state != "running":
                    docker(
                        "start",
                        CONTAINER,
                    )

            except subprocess.CalledProcessError:
                pass


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except Exception as exc:
        print(
            (
                "V10.3 E2E FAILED: "
                f"{type(exc).__name__}: "
                f"{exc}"
            ),
            file=sys.stderr,
        )
        raise