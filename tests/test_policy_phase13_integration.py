from app.api.v1.policy_enforcement import router


def test_phase13_policy_api_surface_is_present() -> None:
    paths = {route.path for route in router.routes}
    assert "/policy/enforce" in paths
    assert "/policy/audit" in paths


def test_policy_endpoints_are_not_publicly_declared_without_dependencies() -> None:
    routes = {route.path: route for route in router.routes}
    for path in ("/policy/enforce", "/policy/audit"):
        dependant = routes[path].dependant
        dependency_names = {
            dependency.name
            for dependency in dependant.dependencies
            if dependency.name
        }
        assert "current_user" in dependency_names
        assert "session" in dependency_names
