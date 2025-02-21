from typing import Dict

from django.http import HttpRequest
from ninja import Router

from auth.dependencies import get_admin_auth, get_user_auth
from auth.schemas import RefreshTokenSchema, TokenSchema, UserCreate, UserLogin, UserOut
from auth.service import AuthService

router = Router(tags=["auth"])
auth_service = AuthService()


@router.post("/register", response={201: UserOut, 400: Dict[str, str]})
def register(request: HttpRequest, user_data: UserCreate):
    """
    Register a new user.
    """
    success, message, user = auth_service.register_user(user_data)
    if success:
        return 201, UserOut.from_orm(user)
    return 400, {"detail": message}


@router.post("/login", response={200: TokenSchema, 401: Dict[str, str]})
def login(request: HttpRequest, login_data: UserLogin):
    """
    Login a user and generate access tokens.
    """
    user = auth_service.authenticate_user(login_data.email, login_data.password)
    if not user:
        return 401, {"detail": "Invalid credentials"}

    tokens = auth_service.create_tokens(user)
    return 200, tokens


@router.post("/refresh", response={200: TokenSchema, 401: Dict[str, str]})
def refresh_token(request: HttpRequest, refresh_data: RefreshTokenSchema):
    """
    Refresh access token using a refresh token.
    """
    tokens = auth_service.refresh_tokens(refresh_data.refresh_token)
    if not tokens:
        return 401, {"detail": "Invalid refresh token"}

    return 200, tokens


@router.post("/logout", auth=get_user_auth(), response={204: None})
def logout(request: HttpRequest):
    """
    Logout a user and invalidate their tokens.
    """
    auth_service.logout_user(str(request.user.id))
    return 204, None


@router.get("/me", auth=get_user_auth(), response=UserOut)
def get_current_user(request: HttpRequest):
    """
    Get current authenticated user information.
    """
    return UserOut.from_orm(request.user)
