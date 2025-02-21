from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field, validator


class ProductBase(Schema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ProductCreate(ProductBase):
    @validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than zero")
        return v


class ProductUpdate(Schema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)

    @validator("price")
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Price must be greater than zero")
        return v


class ProductOut(ProductBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ProductList(Schema):
    items: list[ProductOut]
    count: int
