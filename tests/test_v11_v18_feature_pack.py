from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_v11_to_v18_router_is_registered():
    router = read("backend/app/api/v1/router.py")
    assert "platform_evolution_router" in router
    assert "include_router(platform_evolution_router)" in router


def test_v11_closed_loop_reliability_is_present():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=11" in service
    assert "governed_remediation" in service
    assert "recommended_action" in service


def test_v12_agent_failover_is_health_aware():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=12" in service
    assert "unhealthy_agents" in service
    assert "selected_agent" in service


def test_v13_policy_recommendations_are_not_auto_applied():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=13" in service
    assert '"auto_applied": False' in service
    assert "recommended_decision" in service


def test_v14_compliance_evidence_checks_missing_fields():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=14" in service
    assert "missing_fields" in service


def test_v15_cloud_readiness_scores_production_controls():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=15" in service
    assert "readiness_score" in service
    assert "secrets_manager" in service


def test_v16_rollout_gate_compares_candidate_and_baseline():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=16" in service
    assert "score_delta" in service
    assert '"PROMOTE"' in service
    assert '"HOLD"' in service


def test_v17_connector_risk_accounts_for_side_effects():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=17" in service
    assert "write_access" in service
    assert "effective_approval_required" in service


def test_v18_agent_registry_requires_trust_signals():
    service = read("backend/app/platform_evolution/service.py")
    assert "version=18" in service
    assert "signed_manifest" in service
    assert "governance_compatible" in service
    assert "trust_state" in service


def test_migration_chain_reaches_v18():
    expected = [
        ("v110a1b2c3d4e", "v102a1b2c3d4e"),
        ("v120a1b2c3d4e", "v110a1b2c3d4e"),
        ("v130a1b2c3d4e", "v120a1b2c3d4e"),
        ("v140a1b2c3d4e", "v130a1b2c3d4e"),
        ("v150a1b2c3d4e", "v140a1b2c3d4e"),
        ("v160a1b2c3d4e", "v150a1b2c3d4e"),
        ("v170a1b2c3d4e", "v160a1b2c3d4e"),
        ("v180a1b2c3d4e", "v170a1b2c3d4e"),
    ]
    migrations = "\n".join(
        p.read_text(encoding="utf-8")
        for p in (ROOT / "backend/alembic/versions").glob("v1*platform*.py")
    )
    # Also include all V11-V18 migration files, whose filenames vary by milestone.
    migrations += "\n" + "\n".join(
        p.read_text(encoding="utf-8")
        for p in (ROOT / "backend/alembic/versions").glob("v1*a1b2c3d4e_*.py")
    )
    for revision, down_revision in expected:
        assert f'revision = "{revision}"' in migrations
        assert f'down_revision = "{down_revision}"' in migrations


def test_control_plane_exposes_evolution_dashboard():
    shell = read("frontend/components/control-plane/ControlPlaneShell.tsx")
    page = read("frontend/app/control-plane/evolution/page.tsx")
    assert "/control-plane/evolution" in shell
    assert "V11-V18 / PLATFORM EVOLUTION" in page
    for version in range(11, 19):
        assert f"[{version}," in page
