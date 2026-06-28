from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

from models.schemas import UserPublic
from services.auth_service import decode_access_token, get_user_by_id
from services.user_context import current_user_id

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(credentials=Depends(_bearer)) -> UserPublic:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Authentication required. Please sign in.")
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(401, "Invalid or expired session. Please sign in again.")
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(401, "User not found.")
    return user


async def bind_user_context(user: UserPublic = Depends(get_current_user)) -> UserPublic:
    current_user_id.set(user.id)
    return user
