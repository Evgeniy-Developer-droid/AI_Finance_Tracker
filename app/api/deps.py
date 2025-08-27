from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from fastapi.security import OAuth2PasswordBearer

from app.db.session import async_session
from app.core.config import settings
from app.core.security import decode_access_token
from app.models import User
from sqlalchemy.future import select

# Для login-роуту: url токену
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")  # підлаштуй свій шлях


# Dependency для отримання поточного користувача з JWT токена
async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception
    email: str = payload["sub"]
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
