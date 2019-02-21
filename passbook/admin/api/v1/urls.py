"""passbook admin API URLs"""
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.routers import DefaultRouter

from passbook.admin.api.v1.applications import ApplicationViewSet
from passbook.admin.api.v1.groups import GroupViewSet
from passbook.admin.api.v1.users import UserViewSet

router = DefaultRouter()
router.register('applications', ApplicationViewSet)
router.register('groups', GroupViewSet)
router.register('users', UserViewSet)

SchemaView = get_schema_view(
    openapi.Info(
        title="passbook Administration API",
        default_version='v1',
        description="Internal passbook API for Administration Interface",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.IsAdminUser,),
)

urlpatterns = router.urls + [
    path('swagger.yml', SchemaView.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', SchemaView.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]
app_name = 'passbook.admin'
