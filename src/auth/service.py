from datetime import datetime
from typing import Optional, Tuple

from django.contrib.auth.hashers import check_password
from django.db import IntegrityError

from auth.jwt import JWTHandler
from auth.models import User
from auth.schemas import TokenSchema, UserCreate


class AuthService:
    def __init__(self) -> None:
        self.jwt_handler = JWTHandler()

    def register_user(self, user_data: UserCreate) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user.

        Returns a tuple (success, message, user)
        """
        try:
            user = User(
                email=user_data.email,
                is_admin=user_data.is_admin,
            )
            user.set_password(user_data.password)
            user.save()
            return True, "User registered successfully", user
        except IntegrityError:
            return False, "Email already registered", None

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        """
        try:
            user = User.objects.get(email=email)
            if check_password(password, user.password_hash):
                # Update last login
                user.last_login = datetime.now()
                user.save(update_fields=["last_login"])
                return user
        except User.DoesNotExist:
            pass

        return None

    def create_tokens(self, user: User) -> TokenSchema:
        """
        Create access and refresh tokens for a user.
        """
        access_token = self.jwt_handler.create_access_token(user_id=user.id, is_admin=user.is_admin)
        refresh_token = self.jwt_handler.create_refresh_token(user_id=user.id)

        return TokenSchema(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh_tokens(self, refresh_token: str) -> Optional[TokenSchema]:
        """
        Create new tokens using a refresh token.
        """
        user_id = self.jwt_handler.verify_refresh_token(refresh_token)
        if not user_id:
            return None

        try:
            user = User.objects.get(id=user_id)
            return self.create_tokens(user)
        except User.DoesNotExist:
            return None

    def logout_user(self, user_id: str) -> None:
        """
        Logout a user by invalidating their tokens.
        """
        self.jwt_handler.invalidate_tokens(user_id)
