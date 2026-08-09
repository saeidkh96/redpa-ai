from app.api.v1.events import router


def test_event_api_surface() -> None:
    paths = {route.path for route in router.routes}

    assert "/events" in paths
    assert "/events/flush" in paths
