"""api v3 urls"""
from django.urls import path
from django.views.decorators.cache import cache_page
from drf_spectacular.views import SpectacularAPIView
from rest_framework import routers

from authentik.admin.api.meta import AppsViewSet
from authentik.admin.api.metrics import AdministrationMetricsViewSet
from authentik.admin.api.system import SystemView
from authentik.admin.api.tasks import TaskViewSet
from authentik.admin.api.version import VersionView
from authentik.admin.api.workers import WorkerView
from authentik.api.v3.config import ConfigView
from authentik.api.v3.sentry import SentryTunnelView
from authentik.api.views import APIBrowserView
from authentik.core.api.applications import ApplicationViewSet
from authentik.core.api.authenticated_sessions import AuthenticatedSessionViewSet
from authentik.core.api.groups import GroupViewSet
from authentik.core.api.propertymappings import PropertyMappingViewSet
from authentik.core.api.providers import ProviderViewSet
from authentik.core.api.sources import SourceViewSet
from authentik.core.api.tokens import TokenViewSet
from authentik.core.api.users import UserViewSet
from authentik.crypto.api import CertificateKeyPairViewSet
from authentik.events.api.event import EventViewSet
from authentik.events.api.notification import NotificationViewSet
from authentik.events.api.notification_rule import NotificationRuleViewSet
from authentik.events.api.notification_transport import NotificationTransportViewSet
from authentik.flows.api.bindings import FlowStageBindingViewSet
from authentik.flows.api.flows import FlowViewSet
from authentik.flows.api.stages import StageViewSet
from authentik.flows.views import FlowExecutorView
from authentik.managed.api import ConfigFileViewSet
from authentik.outposts.api.outposts import OutpostViewSet
from authentik.outposts.api.service_connections import (
    DockerServiceConnectionViewSet,
    KubernetesServiceConnectionViewSet,
    ServiceConnectionViewSet,
)
from authentik.policies.api.bindings import PolicyBindingViewSet
from authentik.policies.api.policies import PolicyViewSet
from authentik.policies.dummy.api import DummyPolicyViewSet
from authentik.policies.event_matcher.api import EventMatcherPolicyViewSet
from authentik.policies.expiry.api import PasswordExpiryPolicyViewSet
from authentik.policies.expression.api import ExpressionPolicyViewSet
from authentik.policies.hibp.api import HaveIBeenPwendPolicyViewSet
from authentik.policies.password.api import PasswordPolicyViewSet
from authentik.policies.reputation.api import (
    IPReputationViewSet,
    ReputationPolicyViewSet,
    UserReputationViewSet,
)
from authentik.providers.ldap.api import LDAPOutpostConfigViewSet, LDAPProviderViewSet
from authentik.providers.oauth2.api.provider import OAuth2ProviderViewSet
from authentik.providers.oauth2.api.scope import ScopeMappingViewSet
from authentik.providers.oauth2.api.tokens import AuthorizationCodeViewSet, RefreshTokenViewSet
from authentik.providers.proxy.api import ProxyOutpostConfigViewSet, ProxyProviderViewSet
from authentik.providers.saml.api import SAMLPropertyMappingViewSet, SAMLProviderViewSet
from authentik.sources.ldap.api import LDAPPropertyMappingViewSet, LDAPSourceViewSet
from authentik.sources.oauth.api.source import OAuthSourceViewSet
from authentik.sources.oauth.api.source_connection import UserOAuthSourceConnectionViewSet
from authentik.sources.plex.api.source import PlexSourceViewSet
from authentik.sources.plex.api.source_connection import PlexSourceConnectionViewSet
from authentik.sources.saml.api import SAMLSourceViewSet
from authentik.stages.authenticator_duo.api import (
    AuthenticatorDuoStageViewSet,
    DuoAdminDeviceViewSet,
    DuoDeviceViewSet,
)
from authentik.stages.authenticator_static.api import (
    AuthenticatorStaticStageViewSet,
    StaticAdminDeviceViewSet,
    StaticDeviceViewSet,
)
from authentik.stages.authenticator_totp.api import (
    AuthenticatorTOTPStageViewSet,
    TOTPAdminDeviceViewSet,
    TOTPDeviceViewSet,
)
from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageViewSet
from authentik.stages.authenticator_webauthn.api import (
    AuthenticateWebAuthnStageViewSet,
    WebAuthnAdminDeviceViewSet,
    WebAuthnDeviceViewSet,
)
from authentik.stages.captcha.api import CaptchaStageViewSet
from authentik.stages.consent.api import ConsentStageViewSet, UserConsentViewSet
from authentik.stages.deny.api import DenyStageViewSet
from authentik.stages.dummy.api import DummyStageViewSet
from authentik.stages.email.api import EmailStageViewSet
from authentik.stages.identification.api import IdentificationStageViewSet
from authentik.stages.invitation.api import InvitationStageViewSet, InvitationViewSet
from authentik.stages.password.api import PasswordStageViewSet
from authentik.stages.prompt.api import PromptStageViewSet, PromptViewSet
from authentik.stages.user_delete.api import UserDeleteStageViewSet
from authentik.stages.user_login.api import UserLoginStageViewSet
from authentik.stages.user_logout.api import UserLogoutStageViewSet
from authentik.stages.user_write.api import UserWriteStageViewSet
from authentik.tenants.api import TenantViewSet

router = routers.DefaultRouter()

router.register("admin/system_tasks", TaskViewSet, basename="admin_system_tasks")
router.register("admin/apps", AppsViewSet, basename="apps")
router.register("admin/config_files", ConfigFileViewSet, basename="admin_config_files")

router.register("core/authenticated_sessions", AuthenticatedSessionViewSet)
router.register("core/applications", ApplicationViewSet)
router.register("core/groups", GroupViewSet)
router.register("core/users", UserViewSet)
router.register("core/user_consent", UserConsentViewSet)
router.register("core/tokens", TokenViewSet)
router.register("core/tenants", TenantViewSet)

router.register("outposts/instances", OutpostViewSet)
router.register("outposts/service_connections/all", ServiceConnectionViewSet)
router.register("outposts/service_connections/docker", DockerServiceConnectionViewSet)
router.register("outposts/service_connections/kubernetes", KubernetesServiceConnectionViewSet)
router.register("outposts/proxy", ProxyOutpostConfigViewSet)
router.register("outposts/ldap", LDAPOutpostConfigViewSet)

router.register("flows/instances", FlowViewSet)
router.register("flows/bindings", FlowStageBindingViewSet)

router.register("crypto/certificatekeypairs", CertificateKeyPairViewSet)

router.register("events/events", EventViewSet)
router.register("events/notifications", NotificationViewSet)
router.register("events/transports", NotificationTransportViewSet)
router.register("events/rules", NotificationRuleViewSet)

router.register("sources/all", SourceViewSet)
router.register("sources/user_connections/oauth", UserOAuthSourceConnectionViewSet)
router.register("sources/user_connections/plex", PlexSourceConnectionViewSet)
router.register("sources/ldap", LDAPSourceViewSet)
router.register("sources/saml", SAMLSourceViewSet)
router.register("sources/oauth", OAuthSourceViewSet)
router.register("sources/plex", PlexSourceViewSet)

router.register("policies/all", PolicyViewSet)
router.register("policies/bindings", PolicyBindingViewSet)
router.register("policies/expression", ExpressionPolicyViewSet)
router.register("policies/event_matcher", EventMatcherPolicyViewSet)
router.register("policies/haveibeenpwned", HaveIBeenPwendPolicyViewSet)
router.register("policies/password_expiry", PasswordExpiryPolicyViewSet)
router.register("policies/password", PasswordPolicyViewSet)
router.register("policies/reputation/users", UserReputationViewSet)
router.register("policies/reputation/ips", IPReputationViewSet)
router.register("policies/reputation", ReputationPolicyViewSet)

router.register("providers/all", ProviderViewSet)
router.register("providers/ldap", LDAPProviderViewSet)
router.register("providers/proxy", ProxyProviderViewSet)
router.register("providers/oauth2", OAuth2ProviderViewSet)
router.register("providers/saml", SAMLProviderViewSet)

router.register("oauth2/authorization_codes", AuthorizationCodeViewSet)
router.register("oauth2/refresh_tokens", RefreshTokenViewSet)

router.register("propertymappings/all", PropertyMappingViewSet)
router.register("propertymappings/ldap", LDAPPropertyMappingViewSet)
router.register("propertymappings/saml", SAMLPropertyMappingViewSet)
router.register("propertymappings/scope", ScopeMappingViewSet)

router.register("authenticators/duo", DuoDeviceViewSet)
router.register("authenticators/static", StaticDeviceViewSet)
router.register("authenticators/totp", TOTPDeviceViewSet)
router.register("authenticators/webauthn", WebAuthnDeviceViewSet)
router.register(
    "authenticators/admin/duo",
    DuoAdminDeviceViewSet,
    basename="admin-duodevice",
)
router.register(
    "authenticators/admin/static",
    StaticAdminDeviceViewSet,
    basename="admin-staticdevice",
)
router.register("authenticators/admin/totp", TOTPAdminDeviceViewSet, basename="admin-totpdevice")
router.register(
    "authenticators/admin/webauthn",
    WebAuthnAdminDeviceViewSet,
    basename="admin-webauthndevice",
)

router.register("stages/all", StageViewSet)
router.register("stages/authenticator/duo", AuthenticatorDuoStageViewSet)
router.register("stages/authenticator/static", AuthenticatorStaticStageViewSet)
router.register("stages/authenticator/totp", AuthenticatorTOTPStageViewSet)
router.register("stages/authenticator/validate", AuthenticatorValidateStageViewSet)
router.register("stages/authenticator/webauthn", AuthenticateWebAuthnStageViewSet)
router.register("stages/captcha", CaptchaStageViewSet)
router.register("stages/consent", ConsentStageViewSet)
router.register("stages/deny", DenyStageViewSet)
router.register("stages/email", EmailStageViewSet)
router.register("stages/identification", IdentificationStageViewSet)
router.register("stages/invitation/invitations", InvitationViewSet)
router.register("stages/invitation/stages", InvitationStageViewSet)
router.register("stages/password", PasswordStageViewSet)
router.register("stages/prompt/prompts", PromptViewSet)
router.register("stages/prompt/stages", PromptStageViewSet)
router.register("stages/user_delete", UserDeleteStageViewSet)
router.register("stages/user_login", UserLoginStageViewSet)
router.register("stages/user_logout", UserLogoutStageViewSet)
router.register("stages/user_write", UserWriteStageViewSet)

router.register("stages/dummy", DummyStageViewSet)
router.register("policies/dummy", DummyPolicyViewSet)

urlpatterns = (
    [
        path("", APIBrowserView.as_view(), name="schema-browser"),
    ]
    + router.urls
    + [
        path(
            "admin/metrics/",
            AdministrationMetricsViewSet.as_view(),
            name="admin_metrics",
        ),
        path("admin/version/", VersionView.as_view(), name="admin_version"),
        path("admin/workers/", WorkerView.as_view(), name="admin_workers"),
        path("admin/system/", SystemView.as_view(), name="admin_system"),
        path("root/config/", ConfigView.as_view(), name="config"),
        path(
            "flows/executor/<slug:flow_slug>/",
            FlowExecutorView.as_view(),
            name="flow-executor",
        ),
        path("sentry/", SentryTunnelView.as_view(), name="sentry"),
        path("schema/", cache_page(86400)(SpectacularAPIView.as_view()), name="schema"),
    ]
)
