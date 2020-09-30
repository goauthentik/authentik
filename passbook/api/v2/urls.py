"""api v2 urls"""
from django.urls import path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers

from passbook.api.permissions import CustomObjectPermissions
from passbook.api.v2.messages import MessagesViewSet
from passbook.audit.api import EventViewSet
from passbook.core.api.applications import ApplicationViewSet
from passbook.core.api.groups import GroupViewSet
from passbook.core.api.propertymappings import PropertyMappingViewSet
from passbook.core.api.providers import ProviderViewSet
from passbook.core.api.sources import SourceViewSet
from passbook.core.api.users import UserViewSet
from passbook.crypto.api import CertificateKeyPairViewSet
from passbook.flows.api import FlowStageBindingViewSet, FlowViewSet, StageViewSet
from passbook.outposts.api import OutpostViewSet
from passbook.policies.api import PolicyBindingViewSet, PolicyViewSet
from passbook.policies.dummy.api import DummyPolicyViewSet
from passbook.policies.expiry.api import PasswordExpiryPolicyViewSet
from passbook.policies.expression.api import ExpressionPolicyViewSet
from passbook.policies.group_membership.api import GroupMembershipPolicyViewSet
from passbook.policies.hibp.api import HaveIBeenPwendPolicyViewSet
from passbook.policies.password.api import PasswordPolicyViewSet
from passbook.policies.reputation.api import ReputationPolicyViewSet
from passbook.providers.oauth2.api import OAuth2ProviderViewSet, ScopeMappingViewSet
from passbook.providers.proxy.api import OutpostConfigViewSet, ProxyProviderViewSet
from passbook.providers.saml.api import SAMLPropertyMappingViewSet, SAMLProviderViewSet
from passbook.sources.ldap.api import LDAPPropertyMappingViewSet, LDAPSourceViewSet
from passbook.sources.oauth.api import OAuthSourceViewSet
from passbook.sources.saml.api import SAMLSourceViewSet
from passbook.stages.captcha.api import CaptchaStageViewSet
from passbook.stages.consent.api import ConsentStageViewSet
from passbook.stages.dummy.api import DummyStageViewSet
from passbook.stages.email.api import EmailStageViewSet
from passbook.stages.identification.api import IdentificationStageViewSet
from passbook.stages.invitation.api import InvitationStageViewSet, InvitationViewSet
from passbook.stages.otp_static.api import OTPStaticStageViewSet
from passbook.stages.otp_time.api import OTPTimeStageViewSet
from passbook.stages.otp_validate.api import OTPValidateStageViewSet
from passbook.stages.password.api import PasswordStageViewSet
from passbook.stages.prompt.api import PromptStageViewSet, PromptViewSet
from passbook.stages.user_delete.api import UserDeleteStageViewSet
from passbook.stages.user_login.api import UserLoginStageViewSet
from passbook.stages.user_logout.api import UserLogoutStageViewSet
from passbook.stages.user_write.api import UserWriteStageViewSet

router = routers.DefaultRouter()

router.register("root/messages", MessagesViewSet, basename="messages")
router.register("core/applications", ApplicationViewSet)
router.register("core/groups", GroupViewSet)
router.register("core/users", UserViewSet)
router.register("outposts/outposts", OutpostViewSet)
router.register("outposts/proxy", OutpostConfigViewSet)

router.register("crypto/certificatekeypairs", CertificateKeyPairViewSet)

router.register("audit/events", EventViewSet)

router.register("sources/all", SourceViewSet)
router.register("sources/ldap", LDAPSourceViewSet)
router.register("sources/saml", SAMLSourceViewSet)
router.register("sources/oauth", OAuthSourceViewSet)

router.register("policies/all", PolicyViewSet)
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

router.register("flows/instances", FlowViewSet)
router.register("flows/bindings", FlowStageBindingViewSet)

router.register("stages/dummy", DummyStageViewSet)
router.register("policies/dummy", DummyPolicyViewSet)

info = openapi.Info(
    title="passbook API",
    default_version="v2",
    contact=openapi.Contact(email="hello@beryju.org"),
    license=openapi.License(name="MIT License"),
)
SchemaView = get_schema_view(
    info,
    public=True,
    permission_classes=(CustomObjectPermissions,),
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
