from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import validate_token_type
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = validate_token_type(token, "access")
        subject = payload.get("sub")
        if not subject:
            raise credentials_error
        result = await session.execute(select(User).where(User.username == subject))
        user = result.scalar_one_or_none()
    except JWTError as exc:
        raise credentials_error from exc

    if user is None or not user.is_active:
        raise credentials_error
    return user


async def require_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user


async def require_viewer_or_admin(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.role not in {UserRole.ADMIN, UserRole.VIEWER}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return current_user
