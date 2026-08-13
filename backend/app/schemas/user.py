import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


class UserCreate(BaseModel):
    email: EmailStr

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()

        if not normalized_value:
            return None

        return normalized_value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not any(character.islower() for character in value):
            raise ValueError(
                "Password must contain at least one lowercase letter."
            )

        if not any(character.isupper() for character in value):
            raise ValueError(
                "Password must contain at least one uppercase letter."
            )

        if not any(character.isdigit() for character in value):
            raise ValueError(
                "Password must contain at least one number."
            )

        return value


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )