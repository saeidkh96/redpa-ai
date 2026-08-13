import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database.session import get_db_session
from app.models.user import User
from app.services.user_service import UserService


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)


DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db_session),
]


AccessToken = Annotated[
    str,
    Depends(oauth2_scheme),
]


async def get_current_user(
    token: AccessToken,
    session: DatabaseSession,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )

    try:
        payload = decode_access_token(token)

        subject = payload.get("sub")
        token_type = payload.get("type")

        if subject is None or token_type != "access":
            raise credentials_exception

        user_id = uuid.UUID(subject)

    except (
        jwt.InvalidTokenError,
        ValueError,
        TypeError,
    ) as exception:
        raise credentials_exception from exception

    user = await UserService.get_by_id(
        session=session,
        user_id=user_id,
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )

    return user


CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]