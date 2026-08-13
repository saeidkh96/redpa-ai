from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.schemas.user import (
    UserCreate,
    UserResponse,
)
from app.services.user_service import (
    UserAlreadyExistsError,
    UserService,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register_user(
    user_data: UserCreate,
    session: DatabaseSession,
) -> UserResponse:
    try:
        user = await UserService.create(
            session=session,
            user_data=user_data,
        )

    except UserAlreadyExistsError as exception:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exception),
        ) from exception

    return UserResponse.model_validate(user)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current authenticated user",
)
async def get_me(
    current_user: CurrentUser,
) -> UserResponse:
    return UserResponse.model_validate(current_user)