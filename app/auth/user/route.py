import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.auth.deps import CurrentUser
from app.auth.user.schema import (
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
)
from app.db.session import DbSession
from app.auth.user import service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users")


@router.get("/", response_model=UsersPublic)
async def read_users(session: DbSession, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """
    return await service.get_users_with_pagination(session, skip, limit)


@router.post("/", response_model=UserPublic)
async def create_user(*, session: DbSession, user_in: UserCreate) -> Any:
    """
    Create new user.
    """
    return await service.create_new_user(session, user_in)


@router.post("/signup", response_model=UserPublic)
async def register_user(session: DbSession, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    return await service.register_new_user(session, user_in)


@router.get("/{user_id}", response_model=UserPublic | None)
async def read_user_by_id(
    user_id: UUID, session: DbSession, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    return await service.get_user_by_id(session, user_id, current_user)
