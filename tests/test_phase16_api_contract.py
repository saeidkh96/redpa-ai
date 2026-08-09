from app.api.v1.oauth import router as oauth_router
from app.api.v1.tenants import router as tenant_router


def test_tenant_api_surface() -> None:
    paths = {route.path for route in tenant_router.routes}

    assert "/tenants" in paths
    assert "/tenants/{tenant_id}/members" in paths


def test_oauth_api_surface() -> None:
    paths = {route.path for route in oauth_router.routes}

    assert "/oauth/providers" in paths
    assert "/oauth/{provider}/authorize" in paths
    assert "/oauth/{provider}/callback" in paths
