"""api v2 urls"""
from django.urls import path, re_path
from drf_yasg2 import openapi
from drf_yasg2.views import get_schema_view
from rest_framework import routers
from rest_framework.permissions import AllowAny

from authentik.admin.api.overview import AdministrationOverviewViewSet
from authentik.admin.api.overview_metrics import AdministrationMetricsViewSet
from authentik.admin.api.tasks import TaskViewSet
from authentik.api.v2.config import ConfigsViewSet
from authentik.api.v2.messages import MessagesViewSet
from authentik.audit.api import EventViewSet
from authentik.core.api.applications import ApplicationViewSet
from authentik.core.api.groups import GroupViewSet
from authentik.core.api.propertymappings import PropertyMappingViewSet
from authentik.core.api.providers import ProviderViewSet
from authentik.core.api.sources import SourceViewSet
from authentik.core.api.tokens import TokenViewSet
from authentik.core.api.users import UserViewSet
from authentik.crypto.api import CertificateKeyPairViewSet
from authentik.flows.api import FlowStageBindingViewSet, FlowViewSet, StageViewSet, FlowCacheViewSet
from authentik.outposts.api import (
    DockerServiceConnectionViewSet,
    KubernetesServiceConnectionViewSet,
    OutpostViewSet,
)
from authentik.policies.api import PolicyBindingViewSet, PolicyViewSet, PolicyCacheViewSet
from authentik.policies.dummy.api import DummyPolicyViewSet
from authentik.policies.expiry.api import PasswordExpiryPolicyViewSet
from authentik.policies.expression.api import ExpressionPolicyViewSet
from authentik.policies.group_membership.api import GroupMembershipPolicyViewSet
from authentik.policies.hibp.api import HaveIBeenPwendPolicyViewSet
from authentik.policies.password.api import PasswordPolicyViewSet
from authentik.policies.reputation.api import ReputationPolicyViewSet
from authentik.providers.oauth2.api import OAuth2ProviderViewSet, ScopeMappingViewSet
from authentik.providers.proxy.api import (
    ProxyOutpostConfigViewSet,
    ProxyProviderViewSet,
)
from authentik.providers.saml.api import SAMLPropertyMappingViewSet, SAMLProviderViewSet
from authentik.sources.ldap.api import LDAPPropertyMappingViewSet, LDAPSourceViewSet
from authentik.sources.oauth.api import OAuthSourceViewSet
from authentik.sources.saml.api import SAMLSourceViewSet
from authentik.stages.captcha.api import CaptchaStageViewSet
from authentik.stages.consent.api import ConsentStageViewSet
from authentik.stages.dummy.api import DummyStageViewSet
from authentik.stages.email.api import EmailStageViewSet
from authentik.stages.identification.api import IdentificationStageViewSet
from authentik.stages.invitation.api import InvitationStageViewSet, InvitationViewSet
from authentik.stages.otp_static.api import OTPStaticStageViewSet
from authentik.stages.otp_time.api import OTPTimeStageViewSet
from authentik.stages.otp_validate.api import OTPValidateStageViewSet
from authentik.stages.password.api import PasswordStageViewSet
from authentik.stages.prompt.api import PromptStageViewSet, PromptViewSet
from authentik.stages.user_delete.api import UserDeleteStageViewSet
from authentik.stages.user_login.api import UserLoginStageViewSet
from authentik.stages.user_logout.api import UserLogoutStageViewSet
from authentik.stages.user_write.api import UserWriteStageViewSet

router = routers.DefaultRouter()

router.register("root/messages", MessagesViewSet, basename="messages")
router.register("root/config", ConfigsViewSet, basename="configs")

router.register(
    "admin/overview", AdministrationOverviewViewSet, basename="admin_overview"
)
router.register("admin/metrics", AdministrationMetricsViewSet, basename="admin_metrics")
router.register("admin/system_tasks", TaskViewSet, basename="admin_system_tasks")

router.register("core/applications", ApplicationViewSet)
router.register("core/groups", GroupViewSet)
router.register("core/users", UserViewSet)
router.register("core/tokens", TokenViewSet)

router.register("outposts/outposts", OutpostViewSet)
router.register("outposts/service_connections/docker", DockerServiceConnectionViewSet)
router.register(
    "outposts/service_connections/kubernetes", KubernetesServiceConnectionViewSet
)
router.register("outposts/proxy", ProxyOutpostConfigViewSet)

router.register("flows/instances", FlowViewSet)
router.register("flows/cached", FlowCacheViewSet, basename="flows_cache")
router.register("flows/bindings", FlowStageBindingViewSet)

router.register("crypto/certificatekeypairs", CertificateKeyPairViewSet)

router.register("audit/events", EventViewSet)

router.register("sources/all", SourceViewSet)
router.register("sources/ldap", LDAPSourceViewSet)
router.register("sources/saml", SAMLSourceViewSet)
router.register("sources/oauth", OAuthSourceViewSet)

router.register("policies/all", PolicyViewSet)
router.register("policies/cached", PolicyCacheViewSet, basename="policies_cache")
router.register("policies/bindings", PolicyBindingViewSet)
router.register("policies/expression", ExpressionPolicyViewSet)
router.register("policies/group_membership", GroupMembershipPolicyViewSet)
router.register("policies/haveibeenpwned", HaveIBeenPwendPolicyViewSet)
router.register("policies/password_expiry", PasswordExpiryPolicyViewSet)
router.register("policies/password", PasswordPolicyViewSet)
router.register("policies/reputation", ReputationPolicyViewSet)

router.register("providers/all", ProviderViewSet)
router.register("providers/proxy", ProxyProviderViewSet)
router.register("providers/oauth2", OAuth2ProviderViewSet)
router.register("providers/saml", SAMLProviderViewSet)

router.register("propertymappings/all", PropertyMappingViewSet)
router.register("propertymappings/ldap", LDAPPropertyMappingViewSet)
router.register("propertymappings/saml", SAMLPropertyMappingViewSet)
router.register("propertymappings/scope", ScopeMappingViewSet)

router.register("stages/all", StageViewSet)
router.register("stages/captcha", CaptchaStageViewSet)
router.register("stages/consent", ConsentStageViewSet)
router.register("stages/email", EmailStageViewSet)
router.register("stages/identification", IdentificationStageViewSet)
router.register("stages/invitation", InvitationStageViewSet)
router.register("stages/invitation/invitations", InvitationViewSet)
router.register("stages/otp_static", OTPStaticStageViewSet)
router.register("stages/otp_time", OTPTimeStageViewSet)
router.register("stages/otp_validate", OTPValidateStageViewSet)
router.register("stages/password", PasswordStageViewSet)
router.register("stages/prompt/prompts", PromptViewSet)
router.register("stages/prompt/stages", PromptStageViewSet)
router.register("stages/user_delete", UserDeleteStageViewSet)
router.register("stages/user_login", UserLoginStageViewSet)
router.register("stages/user_logout", UserLogoutStageViewSet)
router.register("stages/user_write", UserWriteStageViewSet)

router.register("stages/dummy", DummyStageViewSet)
router.register("policies/dummy", DummyPolicyViewSet)

info = openapi.Info(
    title="authentik API",
    default_version="v2",
    contact=openapi.Contact(email="hello@beryju.org"),
    license=openapi.License(name="MIT License"),
)
SchemaView = get_schema_view(
    info,
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    re_path(
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
