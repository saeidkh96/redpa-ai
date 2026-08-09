from app.api.v1.policy_enforcement import router


def test_policy_enforcement_api_contract() -> None:
    paths = {route.path for route in router.routes}
    assert "/policy/enforce" in paths
    assert "/policy/audit" in paths
