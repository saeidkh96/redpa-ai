from app.api.v1.model_gateway import router


def test_model_gateway_routes_are_registered() -> None:
    paths = {
        route.path
        for route in router.routes
    }

    assert "/model-gateway/providers" in paths
    assert "/model-gateway/health" in paths
    assert "/model-gateway/circuits" in paths
    assert "/model-gateway/route" in paths
    assert "/model-gateway/invoke" in paths
