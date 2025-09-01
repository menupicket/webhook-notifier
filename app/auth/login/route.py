from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.auth.deps import CurrentUser
from app.core import security
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.user.schema import Token, UserPublic
from app.db.session import DbSession

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
async def login_access_token(
    session: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    Login, get an access token for future requests
    """
    user = await crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user
