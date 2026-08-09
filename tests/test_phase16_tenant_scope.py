import uuid

import pytest

from app.security.tenant_context import (
    TenantContext,
    TenantScopeError,
    assert_same_tenant,
)
from app.services.tenant_service import slugify


def test_tenant_slugify() -> None:
    assert slugify("RedPA Workspace") == "redpa-workspace"


def test_same_tenant_is_allowed() -> None:
    tenant_id = uuid.uuid4()

    assert_same_tenant(
        context=TenantContext(
            tenant_id=tenant_id,
            user_id=uuid.uuid4(),
            role="viewer",
        ),
        resource_tenant_id=tenant_id,
    )


def test_cross_tenant_access_is_blocked() -> None:
    with pytest.raises(TenantScopeError):
        assert_same_tenant(
            context=TenantContext(
                tenant_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                role="viewer",
            ),
            resource_tenant_id=uuid.uuid4(),
        )
