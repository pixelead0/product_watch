from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from auth.api import router as auth_router
from core.api import router as core_router
from products.api import router as products_router
from visits.api import router as visits_router

# Crear API
api = NinjaAPI(
    title="ProductWatch API",
    version="1.0.0",
    description="API for product management and visit tracking",
    openapi_url="/openapi.json",  # Keep OpenAPI schema
)


# Agregar routers
api.add_router("/", core_router)
api.add_router("/auth", auth_router)
api.add_router("/products", products_router)
api.add_router("/visits", visits_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
