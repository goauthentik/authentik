"""Policy variables provided by the policy engine"""

from django.utils.translation import gettext_lazy as _

from authentik.policies.conditional.registry import FACT_HTTP_REQUEST, FACT_USER, registry
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.types import PolicyRequest
from authentik.root.middleware import ClientIPMiddleware

registry.fact(FACT_USER, _("User"), _("The user the policy is evaluated for."))
registry.fact(
    FACT_HTTP_REQUEST,
    _("HTTP request"),
    _("The HTTP request that caused the policy to be evaluated."),
)


@registry.variable(
    "request.client_ip",
    _("Client IP"),
    T.IP,
    requires=[FACT_HTTP_REQUEST],
    description=_("IP address of the client making the request."),
)
def request_client_ip(request: PolicyRequest):
    if not request.http_request:
        return MISSING
    return ClientIPMiddleware.get_client_ip(request.http_request)


@registry.variable(
    "request.user_agent",
    _("User agent"),
    T.STRING,
    requires=[FACT_HTTP_REQUEST],
    description=_("User agent of the client making the request."),
)
def request_user_agent(request: PolicyRequest):
    if not request.http_request:
        return MISSING
    return request.http_request.META.get("HTTP_USER_AGENT", MISSING)


@registry.variable(
    "request.user",
    _("Logged in user"),
    T.model("authentik_core.user"),
    requires=[FACT_HTTP_REQUEST],
    description=_(
        "The user logged in to the browser making the request. Can differ from the user the "
        "policy is evaluated for, for example when an administrator acts on another user. "
        "Not set for anonymous requests."
    ),
)
def request_user(request: PolicyRequest):
    if not request.http_request:
        return MISSING
    user = getattr(request.http_request, "user", None)
    if not user or not user.is_authenticated:
        return MISSING
    return user.pk
