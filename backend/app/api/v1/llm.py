from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser
from app.clients.ollama_client import ollama_client
from app.schemas.ollama import OllamaHealthResponse


router = APIRouter(
    prefix="/llm",
    tags=["LLM"],
)


@router.get(
    "/health",
    response_model=OllamaHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check Ollama availability",
)
async def check_llm_health(
    current_user: CurrentUser,
) -> OllamaHealthResponse:
    return await ollama_client.health_check()