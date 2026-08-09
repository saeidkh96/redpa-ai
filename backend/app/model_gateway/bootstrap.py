from __future__ import annotations

from app.model_gateway.config import ModelGatewayConfig
from app.model_gateway.gateway import ModelGateway
from app.model_gateway.registry import LLMProviderRegistry
from app.model_gateway.reliability import (
    ReliabilityPolicy,
    ReliableProviderExecutor,
)
from app.model_gateway.routing import CompositeRoutingStrategy


def build_model_gateway_registry() -> LLMProviderRegistry:
    config = ModelGatewayConfig.from_environment()
    return LLMProviderRegistry.from_config(config)


def build_model_gateway(
    registry: LLMProviderRegistry | None = None,
) -> ModelGateway:
    registry = registry or build_model_gateway_registry()

    return ModelGateway(
        registry=registry,
        router=CompositeRoutingStrategy.from_environment(),
        executor=ReliableProviderExecutor(
            policy=ReliabilityPolicy(),
        ),
    )


model_gateway_registry = build_model_gateway_registry()
model_gateway = build_model_gateway(model_gateway_registry)
