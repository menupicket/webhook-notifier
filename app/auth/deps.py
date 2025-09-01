from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from app.core import security
from app.core.config import API_V1_STR, SECRET_KEY
from app.db.session import DbSession
from app.auth.user.schema import TokenPayload
from app.models import User


reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{API_V1_STR}/login/access-token")
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: DbSession, token: TokenDep) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
