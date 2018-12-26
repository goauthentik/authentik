"""passbook admin API URLs"""
from rest_framework.routers import DefaultRouter

from passbook.admin.api.v1.groups import GroupViewSet

router = DefaultRouter()
router.register(r'groups', GroupViewSet)

urlpatterns = router.urls
