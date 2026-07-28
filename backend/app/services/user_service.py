import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate


class UserAlreadyExistsError(Exception):
    """
    Raised when attempting to create a duplicate user.
    """


class UserService:
    """
    User persistence and business logic service.
    """

    @staticmethod
    async def get_by_email(
        session: AsyncSession,
        email: str,
    ) -> User | None:
        statement = select(User).where(
            User.email == email.strip().lower(),
        )

        result = await session.execute(statement)

        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> User | None:
        return await session.get(User, user_id)

    @staticmethod
    async def create(
        session: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        normalized_email = str(user_data.email).strip().lower()

        existing_user = await UserService.get_by_email(
            session=session,
            email=normalized_email,
        )

        if existing_user is not None:
            raise UserAlreadyExistsError(
                "A user with this email already exists."
            )

        user = User(
            email=normalized_email,
            full_name=user_data.full_name,
            hashed_password=hash_password(
                user_data.password,
            ),
            is_active=True,
            is_superuser=False,
        )

        session.add(user)

        try:
            await session.commit()
        except IntegrityError as exception:
            await session.rollback()

            raise UserAlreadyExistsError(
                "A user with this email already exists."
            ) from exception

        await session.refresh(user)

        return user