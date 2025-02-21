import pytest
from django.contrib.auth.hashers import check_password

from auth.models import User
from auth.schemas import UserCreate
from auth.service import AuthService


@pytest.mark.django_db
class TestAuthService:
    def test_register_user(self):
        # Setup
        service = AuthService()
        user_data = UserCreate(email="test@example.com", password="testpassword123", is_admin=False)

        # Execute
        success, message, user = service.register_user(user_data)

        # Assert
        assert success is True
        assert "successfully" in message
        assert user is not None
        assert user.email == "test@example.com"
        assert check_password("testpassword123", user.password_hash) is True
        assert user.is_admin is False

    def test_register_duplicate_email(self):
        # Setup
        service = AuthService()
        user_data = UserCreate(email="duplicate@example.com", password="testpassword123", is_admin=False)

        # Create first user
        service.register_user(user_data)

        # Try to create duplicate
        success, message, user = service.register_user(user_data)

        # Assert
        assert success is False
        assert "already registered" in message
        assert user is None

    def test_authenticate_user_success(self):
        # Setup
        service = AuthService()
        user_data = UserCreate(email="auth@example.com", password="authpassword123", is_admin=False)
        service.register_user(user_data)

        # Execute
        user = service.authenticate_user("auth@example.com", "authpassword123")

        # Assert
        assert user is not None
        assert user.email == "auth@example.com"
        assert user.last_login is not None

    def test_authenticate_user_wrong_password(self):
        # Setup
        service = AuthService()
        user_data = UserCreate(email="auth@example.com", password="authpassword123", is_admin=False)
        service.register_user(user_data)

        # Execute
        user = service.authenticate_user("auth@example.com", "wrongpassword")

        # Assert
        assert user is None

    def test_authenticate_user_nonexistent(self):
        # Setup
        service = AuthService()

        # Execute
        user = service.authenticate_user("nonexistent@example.com", "somepassword")

        # Assert
        assert user is None
