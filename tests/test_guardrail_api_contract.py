from app.api.v1.guardrails import router


def test_guardrail_api_contract() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert "/guardrails/evaluate" in paths
    assert "/guardrails/health" in paths
