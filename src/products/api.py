from typing import Dict, List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Router

from auth.dependencies import get_admin_auth
from notifications.service import NotificationService
from products.schemas import ProductCreate, ProductList, ProductOut, ProductUpdate
from products.service import ProductService

router = Router(tags=["products"])
product_service = ProductService()
notification_service = NotificationService()


@router.get("/", response=ProductList)
def list_products(
    request: HttpRequest,
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
):
    """
    List all products with optional filtering and pagination.
    """
    products, total = product_service.get_all_products(skip=skip, limit=limit, name_filter=name)
    return ProductList(items=[ProductOut.from_orm(p) for p in products], count=total)


@router.get("/popular", response=List[ProductOut])
def list_popular_products(request: HttpRequest, limit: int = 5):
    """
    List popular products based on visit counts.
    """
    products = product_service.get_popular_products(limit=limit)
    return [ProductOut.from_orm(p) for p in products]


@router.get("/{product_id}", response={200: ProductOut, 404: Dict[str, str]})
def get_product(request: HttpRequest, product_id: UUID):
    """
    Get a specific product by ID.
    """
    product = product_service.get_product_by_id(product_id)
    if not product:
        return 404, {"detail": "Product not found"}
    return 200, ProductOut.from_orm(product)


@router.post("/", auth=get_admin_auth(), response={201: ProductOut, 400: Dict[str, str]})
def create_product(request: HttpRequest, product_data: ProductCreate):
    """
    Create a new product (admin only).
    """
    product = product_service.create_product(product_data)

    # Send notification about new product
    notification_service.notify_product_created(product.id)

    return 201, ProductOut.from_orm(product)


@router.put("/{product_id}", auth=get_admin_auth(), response={200: ProductOut, 404: Dict[str, str]})
def update_product(request: HttpRequest, product_id: UUID, product_data: ProductUpdate):
    """
    Update an existing product (admin only).
    """
    product = product_service.update_product(product_id, product_data)
    if not product:
        return 404, {"detail": "Product not found"}

    # Send notification about product update
    notification_service.notify_product_updated(product.id, request.user.id)

    return 200, ProductOut.from_orm(product)


@router.delete("/{product_id}", auth=get_admin_auth(), response={204: None, 404: Dict[str, str]})
def delete_product(request: HttpRequest, product_id: UUID):
    """
    Delete a product (admin only).
    """
    success = product_service.delete_product(product_id)
    if not success:
        return 404, {"detail": "Product not found"}
    return 204, None
