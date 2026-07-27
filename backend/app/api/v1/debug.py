from fastapi import APIRouter, HTTPException, Query
from starlette import status

from app.exceptions import AppException


router = APIRouter(
    prefix="/debug",
    tags=["Debug"],
)


@router.get(
    "/app-error",
    summary="Test application exception handling",
)
async def test_application_error() -> None:
    """Raise an expected application exception."""

    raise AppException(
        status_code=status.HTTP_409_CONFLICT,
        code="resource_conflict",
        message="The requested resource is already in use.",
        details={
            "resource": "debug-resource",
        },
    )


@router.get(
    "/http-error",
    summary="Test HTTP exception handling",
)
async def test_http_error() -> None:
    """Raise a standard FastAPI HTTP exception."""

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="The requested debug resource was not found.",
    )


@router.get(
    "/validation-error",
    summary="Test request validation handling",
)
async def test_validation_error(
    number: int = Query(
        ...,
        ge=1,
        le=10,
    ),
) -> dict[str, int]:
    """Return a validated integer."""

    return {
        "number": number,
    }


@router.get(
    "/server-error",
    summary="Test unexpected exception handling",
)
async def test_server_error() -> None:
    """Raise an unexpected exception."""

    raise RuntimeError("Intentional debug server error")