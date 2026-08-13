from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def build_payload(args: argparse.Namespace) -> dict:
    return {
        "baseline_run_id": args.baseline,
        "candidate_run_id": args.candidate,
        "release_label": args.release_label,
        "max_aggregate_drop": args.max_aggregate_drop,
        "max_metric_drop": args.max_metric_drop,
        "minimum_candidate_score": args.minimum_candidate_score,
        "require_candidate_pass": not args.allow_below_run_threshold,
        "metadata": {"source": "release_gate_cli"},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate a RedPA release quality gate and return a CI-friendly exit code.",
    )
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--baseline", required=True, help="Persisted baseline evaluation run UUID")
    parser.add_argument("--candidate", required=True, help="Persisted candidate evaluation run UUID")
    parser.add_argument("--release-label", default=None)
    parser.add_argument("--max-aggregate-drop", type=float, default=0.05)
    parser.add_argument("--max-metric-drop", type=float, default=0.10)
    parser.add_argument("--minimum-candidate-score", type=float, default=0.70)
    parser.add_argument("--allow-below-run-threshold", action="store_true")
    parser.add_argument("--token", default=None)
    args = parser.parse_args()

    url = args.api_url.rstrip("/") + "/api/v1/evaluations/release-gates/ci-check"
    data = json.dumps(build_payload(args)).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    if args.token:
        request.add_header("Authorization", f"Bearer {args.token}")

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            print(json.dumps(body, indent=2))
            return 0
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
            print(json.dumps(body, indent=2))
        except json.JSONDecodeError:
            print(raw, file=sys.stderr)
        if exc.code == 409:
            return 1
        return 2
    except Exception as exc:
        print(f"release gate request failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
