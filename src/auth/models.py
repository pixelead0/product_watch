from uuid import uuid4

from django.contrib.auth.hashers import make_password
from django.db import models

from core.models import BaseModel


class User(BaseModel):
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def __str__(self) -> str:
        return self.email
