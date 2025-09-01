from sqlalchemy.ext.asyncio import AsyncSession as DbSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from uuid import UUID
from fastapi import HTTPException

from app.models import User
from app.auth.user.schema import UserPublic, UserCreate, UserRegister, UsersPublic
from app import crud


async def get_users_with_pagination(
    session: DbSession, skip: int = 0, limit: int = 100
) -> UsersPublic:
    """
    Fetch users with pagination and count total users.
    """
    # Count total users
    count_statement = select(func.count()).select_from(User)
    result = await session.execute(count_statement)
    count = result.scalar_one()

    # Fetch users with pagination
    statement = select(User).offset(skip).limit(limit)
    result = await session.execute(statement)
    users = result.scalars().all()

    # Convert ORM objects to Pydantic models
    users_public = [UserPublic.from_orm(user) for user in users]

    return UsersPublic(data=users_public, count=count)


async def create_new_user(session: DbSession, user_in: UserCreate) -> User:
    """
    Create a new user.
    """
    user = await crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail=f"{user.email} already exists in the system",
        )

    user = await crud.create_user(session=session, user_create=user_in)
    return user


async def register_new_user(session: DbSession, user_in: UserRegister) -> User:
    """
    Register a new user without requiring login.
    """
    user = await crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )

    # Convert `UserRegister` to a dictionary before validation
    user_create_data = user_in.model_dump()  # Convert to dictionary
    user_create = UserCreate.model_validate(
        user_create_data
    )  # Validate against `UserCreate`

    user = await crud.create_user(session=session, user_create=user_create)
    return user


async def get_user_by_id(
    session: DbSession, user_id: UUID, current_user: User
) -> User | None:
    """
    Get a specific user by ID.
    """
    user = await session.get(User, user_id)
    if user == current_user:
        return user

    return None
