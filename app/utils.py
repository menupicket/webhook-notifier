import logging

import jwt
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import SECRET_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[security.ALGORITHM])
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None
