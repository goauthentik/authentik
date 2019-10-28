"""api v2 urls"""
from django.conf.urls import url
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers
from structlog import get_logger

from passbook.api.permissions import CustomObjectPermissions
from passbook.audit.api.events import EventViewSet
from passbook.core.api.applications import ApplicationViewSet
from passbook.core.api.groups import GroupViewSet
from passbook.core.api.invitations import InvitationViewSet
from passbook.core.api.policies import PolicyViewSet
from passbook.core.api.providers import ProviderViewSet
from passbook.core.api.sources import SourceViewSet
from passbook.core.api.users import UserViewSet
from passbook.lib.utils.reflection import get_apps
from passbook.policies.expiry.api import PasswordExpiryPolicyViewSet
from passbook.policies.group.api import GroupMembershipPolicyViewSet
from passbook.policies.hibp.api import HaveIBeenPwendPolicyViewSet
from passbook.policies.matcher.api import FieldMatcherPolicyViewSet
from passbook.policies.password.api import PasswordPolicyViewSet
from passbook.policies.reputation.api import ReputationPolicyViewSet
from passbook.policies.sso.api import SSOLoginPolicyViewSet
from passbook.policies.webhook.api import WebhookPolicyViewSet
from passbook.providers.app_gw.api import ApplicationGatewayProviderViewSet
from passbook.providers.oauth.api import OAuth2ProviderViewSet
from passbook.providers.oidc.api import OpenIDProviderViewSet
from passbook.providers.saml.api import SAMLProviderViewSet
from passbook.sources.ldap.api import LDAPSourceViewSet
from passbook.sources.oauth.api import OAuthSourceViewSet

LOGGER = get_logger()
router = routers.DefaultRouter()

for _passbook_app in get_apps():
    if hasattr(_passbook_app, 'api_mountpoint'):
        for prefix, viewset in _passbook_app.api_mountpoint:
            router.register(prefix, viewset)
        LOGGER.debug("Mounted API URLs", app_name=_passbook_app.name)

router.register('core/applications', ApplicationViewSet)
router.register('core/invitations', InvitationViewSet)
router.register('core/groups', GroupViewSet)
router.register('core/users', UserViewSet)
router.register('audit/events', EventViewSet)
router.register('sources/all', SourceViewSet)
router.register('sources/ldap', LDAPSourceViewSet)
router.register('sources/oauth', OAuthSourceViewSet)
router.register('policies/all', PolicyViewSet)
router.register('policies/passwordexpiry', PasswordExpiryPolicyViewSet)
router.register('policies/groupmembership', GroupMembershipPolicyViewSet)
router.register('policies/haveibeenpwned', HaveIBeenPwendPolicyViewSet)
router.register('policies/fieldmatcher', FieldMatcherPolicyViewSet)
router.register('policies/password', PasswordPolicyViewSet)
router.register('policies/reputation', ReputationPolicyViewSet)
router.register('policies/ssologin', SSOLoginPolicyViewSet)
router.register('policies/webhook', WebhookPolicyViewSet)
router.register('providers/all', ProviderViewSet)
router.register('providers/applicationgateway', ApplicationGatewayProviderViewSet)
router.register('providers/oauth', OAuth2ProviderViewSet)
router.register('providers/openid', OpenIDProviderViewSet)
router.register('providers/saml', SAMLProviderViewSet)

info = openapi.Info(
    title="passbook API",
    default_version='v2',
    # description="Test description",
    # terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="hello@beryju.org"),
    license=openapi.License(name="MIT License"),
)
SchemaView = get_schema_view(
    info,
    public=True,
    permission_classes=(CustomObjectPermissions,),
)

urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$',
        SchemaView.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', SchemaView.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', SchemaView.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
] + router.urls
