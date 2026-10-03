"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import decode_access_token
from app.models import User

security = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    """Settings bound to the running app (allows injection of test settings)."""
    return request.app.state.settings


def get_db(request: Request):
    """Yield a database session for request-scoped work."""
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Return the authenticated user from a bearer token."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("missing subject")
        user = db.get(User, int(user_id))
        if user is None:
            raise ValueError("user not found")
        return user
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials") from exc


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
SessionDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
