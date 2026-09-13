"""Auth endpoints: register, login, current user."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserOut,
)
from ..utils.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from .deps import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


# ==========================================================
# REGISTER
# ==========================================================

@router.post(
    "/register",
    response_model=AuthResponse,
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):

    existing = (
        db.query(User)
        .filter(
            User.email == payload.email.lower()
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this email "
                "already exists"
            ),
        )

    user = User(

        name=payload.name.strip(),

        email=payload.email.lower(),

        password_hash=hash_password(
            payload.password
        ),

        role=payload.role,

        # EN | HI | AS | BN
        preferred_language=(
            payload.preferred_language.upper()
        ),
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return AuthResponse(

        token=create_access_token(
            user.id,
            user.role,
        ),

        user=UserOut.model_validate(user),
    )


# ==========================================================
# LOGIN
# ==========================================================

@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):

    user = (
        db.query(User)
        .filter(
            User.email == payload.email.lower()
        )
        .first()
    )

    if (
        not user
        or not verify_password(
            payload.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return AuthResponse(

        token=create_access_token(
            user.id,
            user.role,
        ),

        user=UserOut.model_validate(user),
    )


# ==========================================================
# CURRENT USER
# ==========================================================

@router.get(
    "/me",
    response_model=UserOut,
)
def me(
    user: User = Depends(get_current_user),
):

    return UserOut.model_validate(user)