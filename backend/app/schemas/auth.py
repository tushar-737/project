from pydantic import BaseModel, EmailStr, Field


# ==========================================================
# SUPPORTED LANGUAGES
# ==========================================================

LANGUAGE_PATTERN = "^(EN|HI|AS|BN)$"


# ==========================================================
# REGISTER REQUEST
# ==========================================================

class RegisterRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=120,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )

    role: str = Field(
        default="FIELD_OFFICER",
        pattern="^(ADMIN|FIELD_OFFICER|CITIZEN)$",
    )

    # EN | HI | AS | BN
    preferred_language: str = Field(
        default="EN",
        pattern=LANGUAGE_PATTERN,
    )


# ==========================================================
# LOGIN REQUEST
# ==========================================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# ==========================================================
# USER RESPONSE
# ==========================================================

class UserOut(BaseModel):

    id: int

    name: str

    email: str

    role: str

    preferred_language: str

    model_config = {
        "from_attributes": True
    }


# ==========================================================
# AUTH RESPONSE
# ==========================================================

class AuthResponse(BaseModel):

    token: str

    user: UserOut