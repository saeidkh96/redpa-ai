from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def post(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the RedPA AI V18.2 real production E2E demo.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--primary", default="research-agent")
    parser.add_argument("--fallback", default="docker-agent")
    parser.add_argument("--task", default="List the running Docker containers and return a concise runtime summary.")
    parser.add_argument("--no-failure", action="store_true")
    parser.add_argument("--approve", action="store_true")
    args = parser.parse_args()

    print("RedPA AI V18.2 — Production E2E Demo")
    print("=" * 48)
    try:
        result = post(f"{args.base_url.rstrip('/')}/api/v1/production-demo/v18.2/run", {
            "task": args.task,
            "primary_agent": args.primary,
            "fallback_agent": args.fallback,
            "inject_primary_failure": not args.no_failure,
            "approval_granted": args.approve,
        })
    except urllib.error.URLError as exc:
        print(f"[ERROR] Could not reach RedPA backend: {exc}")
        return 2

    for stage in result.get("stages", []):
        print(f"[{stage['status']}] Stage {stage['stage']} {stage['name']} — {stage['detail']}")
    print()
    print(f"E2E DEMO: {result.get('status')}")
    print(f"Evidence: {result.get('evidence_path')}")
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
