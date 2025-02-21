from decimal import Decimal
from uuid import uuid4

import pytest
from django.conf import settings

from auth.models import User
from products.models import Product


@pytest.fixture
def admin_user():
    user = User(
        email="admin@example.com",
        is_admin=True,
    )
    user.set_password("adminpassword")
    user.save()
    return user


@pytest.fixture
def normal_user():
    user = User(
        email="user@example.com",
        is_admin=False,
    )
    user.set_password("userpassword")
    user.save()
    return user


@pytest.fixture
def sample_product():
    product = Product.objects.create(
        name="Test Product",
        description="This is a test product",
        price=Decimal("19.99"),
        stock=100,
    )
    return product


@pytest.fixture
def sample_products(db):
    products = []
    for i in range(5):
        product = Product.objects.create(
            name=f"Test Product {i}",
            description=f"This is test product {i}",
            price=Decimal(f"{10 + i}.99"),
            stock=50 + (i * 10),
        )
        products.append(product)
    return products


@pytest.fixture
def mock_redis_client(monkeypatch):
    """Mock Redis client to avoid actual Redis connections in tests"""

    class MockRedis:
        def __init__(self, *args, **kwargs):
            self.storage = {}
            self.expires = {}

        def hmset(self, key, mapping):
            self.storage[key] = mapping
            return True

        def hgetall(self, key):
            return self.storage.get(key, {})

        def expireat(self, key, timestamp):
            self.expires[key] = timestamp
            return True

        def exists(self, key):
            return key in self.storage

        def get(self, key):
            return self.storage.get(key)

        def set(self, key, value, **kwargs):
            self.storage[key] = value
            return True

        def delete(self, *keys):
            for key in keys:
                if key in self.storage:
                    del self.storage[key]
            return len(keys)

        def incr(self, key):
            if key not in self.storage:
                self.storage[key] = 1
            else:
                self.storage[key] += 1
            return self.storage[key]

        def expire(self, key, seconds):
            self.expires[key] = seconds
            return True

    # Replace redis client with mock
    import redis

    monkeypatch.setattr(redis, "Redis", MockRedis)


@pytest.fixture
def mock_sendgrid_client(monkeypatch):
    """Mock SendGrid client to avoid actual email sending in tests"""

    class MockSendGridClient:
        def __init__(self, api_key=None):
            self.api_key = api_key
            self.messages = []
            self.client = self

        class Response:
            def __init__(self, status_code=202):
                self.status_code = status_code
                self.body = None
                self.headers = {}

        def send(self, message):
            self.messages.append(message)
            return self.Response()

        def post(self, request_body=None):
            self.messages.append(request_body)
            return self.Response()

        def mail(self):
            return self

    # Replace SendGrid client with mock
    import sendgrid

    monkeypatch.setattr(sendgrid, "SendGridAPIClient", MockSendGridClient)
