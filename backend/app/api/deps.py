"""Shared API dependencies (auth)."""
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..config import OPEN_DEMO_MODE
from ..database import get_db
from ..models import User
from ..utils.security import decode_access_token

security = HTTPBearer(auto_error=False)


def _user_from_token(db: Session, token: str | None) -> User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    return db.get(User, payload.get("uid"))


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user.

    OPEN_DEMO_MODE: when the prototype runs without a token (e.g. a fresh
    browser), every protected action acts as the seeded ADMIN account so
    live demonstrations in front of judges never hit an auth wall.
    """
    token = credentials.credentials if credentials else None
    user = _user_from_token(db, token)
    if user is None and OPEN_DEMO_MODE:
        user = db.query(User).filter(User.email == "admin@ner.gov.in").first()
        if user is None:
            user = User(name="Admin (demo)", email="admin@ner.gov.in",
                        password_hash="!", role="ADMIN")
            db.add(user)
            db.commit()
        return user
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_roles(*roles: str):
    """Dependency factory: only allow users whose role is listed."""
    def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return _dep
