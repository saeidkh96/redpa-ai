from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx


@dataclass(slots=True)
class Sample:
    latency_ms: float
    success: bool
    status_code: int | None
    error: str | None = None


def percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * ratio))))
    return ordered[index]


async def request_once(client: httpx.AsyncClient, path: str) -> Sample:
    started = time.perf_counter()
    try:
        response = await client.get(path)
        latency = (time.perf_counter() - started) * 1000
        return Sample(latency, response.is_success, response.status_code)
    except httpx.HTTPError as exc:
        latency = (time.perf_counter() - started) * 1000
        return Sample(latency, False, None, str(exc))


async def run(base_url: str, path: str, requests: int, concurrency: int, timeout: float) -> list[Sample]:
    semaphore = asyncio.Semaphore(concurrency)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        async def guarded() -> Sample:
            async with semaphore:
                return await request_once(client, path)
        return await asyncio.gather(*(guarded() for _ in range(requests)))


def main() -> int:
    parser = argparse.ArgumentParser(description="RedPA V8 HTTP load smoke and SLO evidence generator")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--path", default="/api/v1/health")
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--availability-target", type=float, default=0.99)
    parser.add_argument("--p95-target-ms", type=float, default=1000.0)
    parser.add_argument("--output", default="artifacts/load-test-v8.json")
    args = parser.parse_args()

    samples = asyncio.run(run(args.base_url, args.path, args.requests, args.concurrency, args.timeout))
    latencies = [sample.latency_ms for sample in samples]
    success_count = sum(sample.success for sample in samples)
    availability = success_count / len(samples) if samples else 0.0
    p95 = percentile(latencies, 0.95)
    decision = "PASS" if availability >= args.availability_target and p95 <= args.p95_target_ms else "FAIL"

    report = {
        "base_url": args.base_url,
        "path": args.path,
        "requests": len(samples),
        "concurrency": args.concurrency,
        "successful": success_count,
        "availability": availability,
        "latency_ms": {
            "mean": statistics.fmean(latencies) if latencies else 0.0,
            "p50": percentile(latencies, 0.50),
            "p95": p95,
            "p99": percentile(latencies, 0.99),
            "max": max(latencies, default=0.0),
        },
        "targets": {
            "availability": args.availability_target,
            "p95_latency_ms": args.p95_target_ms,
        },
        "decision": decision,
        "samples": [asdict(sample) for sample in samples],
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "samples"}, indent=2))
    return 0 if decision == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
