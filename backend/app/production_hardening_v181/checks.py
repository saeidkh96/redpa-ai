from __future__ import annotations

from typing import Any

def check_stage_1(e: dict[str, Any]) -> tuple[bool, str]:
    ok = bool(e.get("integration", {}).get("v12_v18_chain_verified"))
    return ok, "V12-V18 integration chain verified" if ok else "V12-V18 integration chain not verified"

def check_stage_2(e: dict[str, Any]) -> tuple[bool, str]:
    migration = e.get("migration", {})
    ok = migration.get("head") == "v270a1b2c3d4e" and bool(migration.get("clean_upgrade_verified"))
    return ok, "Migration chain reaches v270 head from clean baseline" if ok else "Migration-chain verification incomplete"

def check_stage_3(e: dict[str, Any]) -> tuple[bool, str]:
    api = e.get("api_e2e", {})
    ok = bool(api.get("auth")) and int(api.get("successful_flows", 0)) >= 6
    return ok, "Authenticated API E2E flows verified" if ok else "API E2E coverage incomplete"

def check_stage_4(e: dict[str, Any]) -> tuple[bool, str]:
    p = e.get("persistence", {})
    ok = bool(p.get("restart_survival")) and bool(p.get("idempotency_survival"))
    return ok, "Persistence survives process restart" if ok else "Persistence/restart evidence incomplete"

def check_stage_5(e: dict[str, Any]) -> tuple[bool, str]:
    f = e.get("failure_injection", {})
    ok = bool(f.get("fail_closed")) and bool(f.get("no_false_resolution"))
    return ok, "Failure injection remains fail-closed" if ok else "Failure-path safety not proven"

def check_stage_6(e: dict[str, Any]) -> tuple[bool, str]:
    s = e.get("security", {})
    ok = all(bool(s.get(k)) for k in (
        "approval_boundary",
        "connector_write_boundary",
        "trusted_agent_boundary",
        "policy_boundary",
    ))
    return ok, "Security/governance boundaries verified" if ok else "Security boundary evidence incomplete"

def check_stage_7(e: dict[str, Any]) -> tuple[bool, str]:
    d = e.get("docker", {})
    ok = int(d.get("healthy_services", 0)) >= int(d.get("required_services", 1)) and bool(d.get("backend_healthy"))
    return ok, "Docker runtime health verified" if ok else "Docker runtime not fully healthy"

def check_stage_8(e: dict[str, Any]) -> tuple[bool, str]:
    o = e.get("observability", {})
    ok = bool(o.get("metrics")) and bool(o.get("logs")) and bool(o.get("traces"))
    return ok, "Metrics/logs/traces verified" if ok else "Observability coverage incomplete"

def check_stage_9(e: dict[str, Any]) -> tuple[bool, str]:
    r = e.get("release_evidence", {})
    ok = bool(r.get("machine_readable")) and bool(r.get("persisted")) and bool(r.get("exportable"))
    return ok, "Release evidence is persisted and exportable" if ok else "Release evidence incomplete"

def check_stage_10(e: dict[str, Any]) -> tuple[bool, str]:
    g = e.get("regression", {})
    ok = int(g.get("tests_passed", 0)) >= 418 and bool(g.get("all_stage_gates_passed"))
    return ok, "Final regression gate passed" if ok else "Final regression gate failed"
