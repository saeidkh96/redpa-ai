from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.services.user_service import UserService


class AuthService:
    """
    Authentication business logic.
    """

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        email: str,
        password: str,
    ) -> User | None:
        user = await UserService.get_by_email(
            session=session,
            email=email,
        )

        if user is None:
            return None

        if not verify_password(
            plain_password=password,
            hashed_password=user.hashed_password,
        ):
            return None

        if not user.is_active:
            return None

        return user