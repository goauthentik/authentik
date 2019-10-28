"""api v2 urls"""
from rest_framework import routers

from passbook.audit.api.events import EventViewSet
from passbook.core.api.applications import ApplicationViewSet
from passbook.core.api.groups import GroupViewSet
from passbook.core.api.invitations import InvitationViewSet
from passbook.core.api.users import UserViewSet

router = routers.DefaultRouter()
router.register('core/applications', ApplicationViewSet)
router.register('core/invitations', InvitationViewSet)
router.register('core/groups', GroupViewSet)
router.register('core/users', UserViewSet)
router.register('audit/events', EventViewSet)
urlpatterns = router.urls
