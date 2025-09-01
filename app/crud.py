from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.auth.user.schema import UserCreate
from app.models import User


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    # Create a new User object with the hashed password
    db_obj = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        is_active=user_create.is_active,
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.execute(statement)
    session_user = result.scalars().first()
    return session_user


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    else:
        db_password = db_user.hashed_password
        if not verify_password(password, db_password):  # type: ignore
            return None
    return db_user
