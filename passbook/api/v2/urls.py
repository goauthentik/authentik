"""api v2 urls"""
from django.conf.urls import url
from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers
from structlog import get_logger

from passbook.api.permissions import CustomObjectPermissions
from passbook.audit.api import EventViewSet
from passbook.core.api.applications import ApplicationViewSet
from passbook.core.api.factors import FactorViewSet
from passbook.core.api.groups import GroupViewSet
from passbook.core.api.invitations import InvitationViewSet
from passbook.core.api.policies import PolicyViewSet
from passbook.core.api.propertymappings import PropertyMappingViewSet
from passbook.core.api.providers import ProviderViewSet
from passbook.core.api.sources import SourceViewSet
from passbook.core.api.users import UserViewSet
from passbook.factors.captcha.api import CaptchaFactorViewSet
from passbook.factors.dummy.api import DummyFactorViewSet
from passbook.factors.email.api import EmailFactorViewSet
from passbook.factors.otp.api import OTPFactorViewSet
from passbook.factors.password.api import PasswordFactorViewSet
from passbook.lib.utils.reflection import get_apps
from passbook.policies.expiry.api import PasswordExpiryPolicyViewSet
from passbook.policies.expression.api import ExpressionPolicyViewSet
from passbook.policies.hibp.api import HaveIBeenPwendPolicyViewSet
from passbook.policies.password.api import PasswordPolicyViewSet
from passbook.policies.reputation.api import ReputationPolicyViewSet
from passbook.policies.webhook.api import WebhookPolicyViewSet
from passbook.providers.app_gw.api import ApplicationGatewayProviderViewSet
from passbook.providers.oauth.api import OAuth2ProviderViewSet
from passbook.providers.oidc.api import OpenIDProviderViewSet
from passbook.providers.saml.api import SAMLPropertyMappingViewSet, SAMLProviderViewSet
from passbook.sources.ldap.api import LDAPPropertyMappingViewSet, LDAPSourceViewSet
from passbook.sources.oauth.api import OAuthSourceViewSet

LOGGER = get_logger()
router = routers.DefaultRouter()

for _passbook_app in get_apps():
    if hasattr(_passbook_app, "api_mountpoint"):
        for prefix, viewset in _passbook_app.api_mountpoint:
            router.register(prefix, viewset)
        LOGGER.debug("Mounted API URLs", app_name=_passbook_app.name)

router.register("core/applications", ApplicationViewSet)
router.register("core/invitations", InvitationViewSet)
router.register("core/groups", GroupViewSet)
router.register("core/users", UserViewSet)
router.register("audit/events", EventViewSet)
router.register("sources/all", SourceViewSet)
router.register("sources/ldap", LDAPSourceViewSet)
router.register("sources/oauth", OAuthSourceViewSet)
router.register("policies/all", PolicyViewSet)
router.register("policies/passwordexpiry", PasswordExpiryPolicyViewSet)
router.register("policies/haveibeenpwned", HaveIBeenPwendPolicyViewSet)
router.register("policies/password", PasswordPolicyViewSet)
router.register("policies/reputation", ReputationPolicyViewSet)
router.register("policies/webhook", WebhookPolicyViewSet)
router.register("policies/expression", ExpressionPolicyViewSet)
router.register("providers/all", ProviderViewSet)
router.register("providers/applicationgateway", ApplicationGatewayProviderViewSet)
router.register("providers/oauth", OAuth2ProviderViewSet)
router.register("providers/openid", OpenIDProviderViewSet)
router.register("providers/saml", SAMLProviderViewSet)
router.register("propertymappings/all", PropertyMappingViewSet)
router.register("propertymappings/ldap", LDAPPropertyMappingViewSet)
router.register("propertymappings/saml", SAMLPropertyMappingViewSet)
router.register("factors/all", FactorViewSet)
router.register("factors/captcha", CaptchaFactorViewSet)
router.register("factors/dummy", DummyFactorViewSet)
router.register("factors/email", EmailFactorViewSet)
router.register("factors/otp", OTPFactorViewSet)
router.register("factors/password", PasswordFactorViewSet)

info = openapi.Info(
    title="passbook API",
    default_version="v2",
    # description="Test description",
    # terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="hello@beryju.org"),
    license=openapi.License(name="MIT License"),
)
SchemaView = get_schema_view(
    info, public=True, permission_classes=(CustomObjectPermissions,),
)

urlpatterns = [
    url(
        r"^swagger(?P<format>\.json|\.yaml)$",
        SchemaView.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        SchemaView.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", SchemaView.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
] + router.urls
