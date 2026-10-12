import httpx
import pytest

from app.clients.n8n_client import N8NClient, N8NError


@pytest.mark.asyncio
async def test_rejects_non_allowlisted_workflow():
    client = N8NClient()
    client.allowed = {"approved-workflow"}

    with pytest.raises(N8NError, match="not allowlisted"):
        await client.execute("unknown-workflow", {})


@pytest.mark.asyncio
async def test_rejects_invalid_workflow_name():
    client = N8NClient()
    client.allowed = {"../invalid"}

    with pytest.raises(N8NError, match="Invalid workflow name"):
        await client.execute("../invalid", {})


@pytest.mark.asyncio
async def test_successful_workflow_execution(monkeypatch):
    client = N8NClient()
    client.allowed = {"test-workflow"}
    client.base_url = "http://n8n.test"

    async def handler(request):
        assert request.url.path == "/webhook/test-workflow"
        return httpx.Response(
            200,
            json={"status": "success"},
        )

    transport = httpx.MockTransport(handler)

    original_client = httpx.AsyncClient

    def mocked_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mocked_client)

    result = await client.execute(
        "test-workflow",
        {"message": "Hello"},
    )

    assert result == {"status": "success"}


@pytest.mark.asyncio
async def test_n8n_http_error(monkeypatch):
    client = N8NClient()
    client.allowed = {"test-workflow"}

    transport = httpx.MockTransport(
        lambda request: httpx.Response(500)
    )

    original_client = httpx.AsyncClient

    def mocked_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mocked_client)

    with pytest.raises(N8NError, match="execution failed"):
        await client.execute("test-workflow", {})
