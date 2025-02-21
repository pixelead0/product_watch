from decimal import Decimal
from uuid import uuid4

import pytest
from django.core.cache import cache

from products.models import Product
from products.schemas import ProductCreate, ProductUpdate
from products.service import ProductService


@pytest.mark.django_db
class TestProductService:
    def test_create_product(self):
        # Setup
        service = ProductService()
        product_data = ProductCreate(
            name="New Test Product", description="A test product created for testing", price=Decimal("29.99"), stock=50
        )

        # Execute
        product = service.create_product(product_data)

        # Assert
        assert product is not None
        assert product.name == "New Test Product"
        assert product.description == "A test product created for testing"
        assert product.price == Decimal("29.99")
        assert product.stock == 50

    def test_get_product_by_id(self, sample_product):
        # Setup
        service = ProductService()
        product_id = sample_product.id

        # Execute
        product = service.get_product_by_id(product_id)

        # Assert
        assert product is not None
        assert product.id == product_id
        assert product.name == sample_product.name

    def test_get_product_by_id_nonexistent(self):
        # Setup
        service = ProductService()
        nonexistent_id = uuid4()

        # Execute
        product = service.get_product_by_id(nonexistent_id)

        # Assert
        assert product is None

    def test_update_product(self, sample_product):
        # Setup
        service = ProductService()
        product_id = sample_product.id
        update_data = ProductUpdate(name="Updated Product Name", price=Decimal("24.99"))

        # Execute
        updated_product = service.update_product(product_id, update_data)

        # Assert
        assert updated_product is not None
        assert updated_product.id == product_id
        assert updated_product.name == "Updated Product Name"
        assert updated_product.price == Decimal("24.99")
        # Should not change fields not included in update
        assert updated_product.description == sample_product.description
        assert updated_product.stock == sample_product.stock

    def test_update_nonexistent_product(self):
        # Setup
        service = ProductService()
        nonexistent_id = uuid4()
        update_data = ProductUpdate(name="Updated Name")

        # Execute
        updated_product = service.update_product(nonexistent_id, update_data)

        # Assert
        assert updated_product is None

    def test_delete_product(self, sample_product):
        # Setup
        service = ProductService()
        product_id = sample_product.id

        # Execute
        success = service.delete_product(product_id)

        # Assert
        assert success is True
        assert Product.objects.filter(id=product_id).exists() is False

    def test_delete_nonexistent_product(self):
        # Setup
        service = ProductService()
        nonexistent_id = uuid4()

        # Execute
        success = service.delete_product(nonexistent_id)

        # Assert
        assert success is False

    def test_get_all_products(self, sample_products):
        # Setup
        service = ProductService()

        # Execute
        products, total = service.get_all_products()

        # Assert
        assert len(products) == 5
        assert total == 5

    def test_get_all_products_with_name_filter(self, sample_products):
        # Setup
        service = ProductService()

        # Execute - should match "Test Product 1"
        products, total = service.get_all_products(name_filter="Product 1")

        # Assert
        assert len(products) == 1
        assert total == 1
        assert products[0].name == "Test Product 1"

    def test_get_all_products_with_pagination(self, sample_products):
        # Setup
        service = ProductService()

        # Execute
        products, total = service.get_all_products(skip=2, limit=2)

        # Assert
        assert len(products) == 2
        assert total == 5  # Total should still be 5, despite pagination

    def test_product_cache(self, sample_product, monkeypatch):
        # Setup
        service = ProductService()
        product_id = sample_product.id

        # Clear cache to start fresh
        cache.clear()

        # Track database queries
        query_count = [0]
        original_get = Product.objects.get

        def mock_get(*args, **kwargs):
            query_count[0] += 1
            return original_get(*args, **kwargs)

        monkeypatch.setattr(Product.objects, "get", mock_get)

        # Execute - First call should hit database
        product1 = service.get_product_by_id(product_id)
        first_query_count = query_count[0]

        # Execute - Second call should use cache
        product2 = service.get_product_by_id(product_id)
        second_query_count = query_count[0]

        # Assert
        assert product1 is not None
        assert product1.id == product_id
        assert product2 is not None
        assert product2.id == product_id
        assert first_query_count == 1  # First call should hit database
        assert second_query_count == 1  # Second call should use cache (no new queries)

    def test_cache_invalidation_on_update(self, sample_product):
        # Setup
        service = ProductService()
        product_id = sample_product.id

        # Cache product
        service.get_product_by_id(product_id)

        # Execute - Update product
        update_data = ProductUpdate(name="Updated After Cache")
        updated_product = service.update_product(product_id, update_data)

        # Get from cache again - should be updated
        product_after_update = service.get_product_by_id(product_id)

        # Assert
        assert updated_product.name == "Updated After Cache"
        assert product_after_update.name == "Updated After Cache"

    def test_get_popular_products(self, sample_products):
        # Setup
        service = ProductService()

        # Execute
        popular_products = service.get_popular_products(limit=3)

        # Assert
        assert len(popular_products) <= 3

        # Test with different limit
        all_popular_products = service.get_popular_products(limit=10)
        assert len(all_popular_products) <= 10

    def test_cache_popular_products(self, sample_products):
        # Setup
        service = ProductService()

        # Clear cache to start fresh
        cache.clear()

        # Execute - Primera llamada (debería ir a la base de datos)
        products1 = service.get_popular_products()

        # Crear un nuevo producto para verificar el caché
        new_product = Product.objects.create(
            name="NEW PRODUCT AFTER CACHE",
            description="This product should not appear in cached results",
            price=Decimal("99.99"),
            stock=999,
        )

        # Execute - Segunda llamada (debería usar caché)
        products2 = service.get_popular_products()

        # Verificar que products2 viene de la caché (no contiene el nuevo producto)
        assert not any(p.name == "NEW PRODUCT AFTER CACHE" for p in products2)

        # Limpiar caché y verificar que ahora sí incluye el nuevo producto
        cache.clear()
        products3 = service.get_popular_products()
        assert any(p.name == "NEW PRODUCT AFTER CACHE" for p in products3)
