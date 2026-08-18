from app.production_hardening_v181.validation import validate_release_evidence

def full_evidence():
    return {
        "integration": {"v12_v18_chain_verified": True},
        "migration": {"head": "v270a1b2c3d4e", "clean_upgrade_verified": True},
        "api_e2e": {"auth": True, "successful_flows": 8},
        "persistence": {"restart_survival": True, "idempotency_survival": True},
        "failure_injection": {"fail_closed": True, "no_false_resolution": True},
        "security": {
            "approval_boundary": True,
            "connector_write_boundary": True,
            "trusted_agent_boundary": True,
            "policy_boundary": True,
        },
        "docker": {"healthy_services": 12, "required_services": 12, "backend_healthy": True},
        "observability": {"metrics": True, "logs": True, "traces": True},
        "release_evidence": {"machine_readable": True, "persisted": True, "exportable": True},
        "regression": {"tests_passed": 418, "all_stage_gates_passed": True},
    }

def test_v181_all_ten_stages_pass_with_complete_evidence():
    report = validate_release_evidence(full_evidence())
    assert len(report.stages) == 10
    assert report.overall_status == "PASS"
    assert all(stage.status == "pass" for stage in report.stages)

def test_v181_failure_injection_failure_fails_release():
    e = full_evidence()
    e["failure_injection"]["fail_closed"] = False
    report = validate_release_evidence(e)
    assert report.overall_status == "FAIL"
    assert report.stages[4].status == "fail"

def test_v181_regression_gate_requires_current_baseline():
    e = full_evidence()
    e["regression"]["tests_passed"] = 417
    report = validate_release_evidence(e)
    assert report.overall_status == "FAIL"
    assert report.stages[9].status == "fail"
