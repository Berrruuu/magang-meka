from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Carfix API",
        default_version='v1',
        description="Dokumentasi API Carfix",
        contact=openapi.Contact(email="admin@carfix.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    url="http://127.0.0.1:8000"
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/dashboard/v1/', include('kpi.urls')),

    # swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
]
