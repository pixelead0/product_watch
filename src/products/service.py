from typing import List, Optional, Tuple
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.db.models.query import QuerySet

from products.models import Product
from products.schemas import ProductCreate, ProductUpdate


class ProductService:
    @staticmethod
    def get_product_by_id(product_id: UUID) -> Optional[Product]:
        """
        Get product by id, using cache if available
        """
        cache_key = f"product:{product_id}"
        cached_product = cache.get(cache_key)

        if cached_product:
            return cached_product

        try:
            product = Product.objects.get(id=product_id)
            # Cache product for future requests
            cache.set(cache_key, product, timeout=settings.PRODUCT_CACHE_TIMEOUT)
            return product
        except Product.DoesNotExist:
            return None

    @staticmethod
    def get_all_products(
        skip: int = 0, limit: int = 100, name_filter: Optional[str] = None
    ) -> Tuple[List[Product], int]:
        """
        Get all products with optional pagination and filtering
        """
        queryset = Product.objects.all()

        if name_filter:
            queryset = queryset.filter(name__icontains=name_filter)

        total = queryset.count()
        products = queryset.order_by("-created_at")[skip : skip + limit]

        return list(products), total

    @staticmethod
    def create_product(product_data: ProductCreate) -> Product:
        """
        Create a new product
        """
        product = Product(**product_data.dict())
        product.save()
        return product

    @staticmethod
    def update_product(product_id: UUID, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update a product
        """
        try:
            product = Product.objects.get(id=product_id)

            # Update product fields if provided
            update_data = product_data.dict(exclude_unset=True)
            for key, value in update_data.items():
                setattr(product, key, value)

            product.save()

            # Invalidate cache
            cache_key = f"product:{product_id}"
            cache.delete(cache_key)

            return product
        except Product.DoesNotExist:
            return None

    @staticmethod
    def delete_product(product_id: UUID) -> bool:
        """
        Delete a product
        """
        try:
            product = Product.objects.get(id=product_id)
            product.delete()

            # Invalidate cache
            cache_key = f"product:{product_id}"
            cache.delete(cache_key)

            return True
        except Product.DoesNotExist:
            return False

    @staticmethod
    def get_popular_products(limit: int = 5) -> List[Product]:
        """
        Get popular products based on visit counts
        Uses cache for better performance
        """
        cache_key = f"popular_products:{limit}"
        cached_products = cache.get(cache_key)

        if cached_products:
            return cached_products

        # Convertir QuerySet a lista para forzar la ejecución
        products = list(Product.objects.all().order_by("-created_at")[:limit])

        # Cache popular products
        cache.set(cache_key, products, timeout=settings.PRODUCT_CACHE_TIMEOUT)

        return products
