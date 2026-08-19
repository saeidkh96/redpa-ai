from app.api.v1.platform_evolution import router as platform_evolution_router
from app.api.v1.adaptive_governance_v13 import (
    router as adaptive_governance_v13_router,
)
from app.api.v1.security_compliance_v14 import (
    router as security_compliance_v14_router,
)
from app.api.v1.cloud_readiness_v15 import (
    router as cloud_readiness_v15_router,
)
from app.api.v1.continuous_evaluation_v16 import (
    router as continuous_evaluation_v16_router,
)
from app.api.v1.enterprise_integration_v17 import (
    router as enterprise_integration_v17_router,
)
from app.api.v1.trusted_agents_v18 import (
    router as trusted_agents_v18_router,
)
from app.api.v1.production_hardening_v181 import (
    router as production_hardening_v181_router,
)
from app.api.v1.production_demo_v182 import (
    router as production_demo_v182_router,
)
from app.api.v1.governance_v10 import router as governance_v10_router
from app.api.v1.operations_v9 import router as operations_v9_router
from app.api.v1.analytics_v8 import router as analytics_v8_router
from app.api.v1.connectors_v8 import router as connectors_v8_router
from app.api.v1.operations_v8 import router as operations_v8_router
from app.api.v1.enterprise_research import router as enterprise_research_router
from app.api.v1.production_ai import router as production_ai_router
from app.api.v1.platform_v4 import router as platform_v4_router
from app.api.v1.events import router as events_router
from app.api.v1.oauth import router as oauth_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1 import model_gateway
from app.api.v1 import evaluations
from app.api.v1.performance import router as performance_router
from app.api.v1.platform_health import router as platform_health_router
from app.api.v1.background_jobs import router as background_jobs_router
from app.agent_memory.dashboard import router as agent_memory_dashboard_router
from app.api.v1.agent_memory_admin import router as agent_memory_admin_router
from app.api.v1.agent_memory import router as agent_memory_router
from app.api.v1.durable_workflows import router as durable_workflows_router
from app.api.v1.distributed_agents import router as distributed_agents_router
from app.api.v1.guardrails import router as guardrails_router
from app.api.v1.policy_enforcement import router as policy_enforcement_router
from fastapi import APIRouter

from app.api.v1.multi_agents import router as multi_agents_router
from app.api.v1.remote_agents import router as remote_agents_router
from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.conversations import (
    router as conversations_router,
)
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.llm import router as llm_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.messages import router as messages_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.tools import router as tools_router
from app.api.v1.users import router as users_router

from app.api.v1.mcp import router as mcp_router
from app.api.v1.unified_tools import router as unified_tools_router

api_router = APIRouter()
api_router.include_router(
    platform_health_router,
)
api_router.include_router(
    performance_router,
)
api_router.include_router(
    monitoring_router,
)
api_router.include_router(background_jobs_router)
api_router.include_router(agent_memory_admin_router)
api_router.include_router(agent_memory_dashboard_router)
api_router.include_router(agent_memory_router)
api_router.include_router(durable_workflows_router)
api_router.include_router(distributed_agents_router)
api_router.include_router(multi_agents_router)
api_router.include_router(remote_agents_router)
api_router.include_router(agents_router)

api_router.include_router(
    health_router,
)
api_router.include_router(
    auth_router,
)
api_router.include_router(
    users_router,
)
api_router.include_router(
    conversations_router,
)
api_router.include_router(
    messages_router,
)
api_router.include_router(
    chat_router,
)
api_router.include_router(
    llm_router,
)
api_router.include_router(
    documents_router,
)
api_router.include_router(
    reviews_router,
)
api_router.include_router(
    tools_router,
)
api_router.include_router(
    mcp_router,
)

api_router.include_router(
    unified_tools_router,
)

api_router.include_router(evaluations.router)


api_router.include_router(model_gateway.router)


api_router.include_router(guardrails_router)


api_router.include_router(policy_enforcement_router)


api_router.include_router(tenants_router)

api_router.include_router(oauth_router)


api_router.include_router(events_router)


api_router.include_router(platform_v4_router)

api_router.include_router(production_ai_router)

api_router.include_router(enterprise_research_router)

api_router.include_router(analytics_v8_router)
api_router.include_router(connectors_v8_router)
api_router.include_router(operations_v8_router)
api_router.include_router(operations_v9_router)

api_router.include_router(governance_v10_router)

api_router.include_router(platform_evolution_router)
api_router.include_router(adaptive_governance_v13_router)
api_router.include_router(security_compliance_v14_router)
api_router.include_router(cloud_readiness_v15_router)
api_router.include_router(continuous_evaluation_v16_router)
api_router.include_router(enterprise_integration_v17_router)
api_router.include_router(trusted_agents_v18_router)
api_router.include_router(production_hardening_v181_router)
api_router.include_router(production_demo_v182_router)
