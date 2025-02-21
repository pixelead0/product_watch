from datetime import datetime
from typing import Optional
from uuid import UUID

from ninja import Schema
from pydantic import EmailStr, Field


class UserCreate(Schema):
    email: EmailStr
    password: str = Field(..., min_length=8)
    is_admin: bool = False


class UserLogin(Schema):
    email: EmailStr
    password: str


class UserOut(Schema):
    id: UUID
    email: EmailStr
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenSchema(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(Schema):
    refresh_token: str


class TokenPayload(Schema):
    sub: str  # usuario ID
    exp: int
    iat: int
    is_admin: bool
