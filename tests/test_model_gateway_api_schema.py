from app.schemas.model_gateway import (
    GatewayInvokeRequest,
    GatewayRoutePreviewRequest,
)


def test_gateway_invoke_request_accepts_messages() -> None:
    request = GatewayInvokeRequest.model_validate(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
            "agent_id": "research-agent",
            "capability": "chat",
        }
    )

    assert request.agent_id == "research-agent"
    assert request.capability.value == "chat"


def test_gateway_route_preview_defaults_to_chat() -> None:
    request = GatewayRoutePreviewRequest()

    assert request.capability.value == "chat"
