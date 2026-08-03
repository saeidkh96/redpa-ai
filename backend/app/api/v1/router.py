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
from app.api.v1.messages import router as messages_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.tools import router as tools_router
from app.api.v1.users import router as users_router

from app.api.v1.mcp import router as mcp_router
from app.api.v1.unified_tools import router as unified_tools_router

api_router = APIRouter()
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
