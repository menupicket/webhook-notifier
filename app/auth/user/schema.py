from uuid import UUID
from pydantic import ConfigDict, EmailStr, BaseModel, Field


PASSWORD_MIN_LEN = 6
PASSWORD_MAX_LEN = 40


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False


# Shared properties
class UserBase(BaseModel):
    email: EmailStr = Field(max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)


class UserRegister(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class UsersPublic(BaseModel):
    data: list[UserPublic]
    count: int


# JSON payload containing access token
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(BaseModel):
    sub: str | None = None


class NewPassword(BaseModel):
    token: str
    new_password: str = Field(min_length=PASSWORD_MIN_LEN, max_length=PASSWORD_MAX_LEN)


# Generic message
class Message(BaseModel):
    message: str
