"""Policy variables provided by the OAuth2 provider"""

from django.utils.translation import gettext_lazy as _

from authentik.policies.conditional.registry import registry
from authentik.policies.conditional.types import MISSING, T
from authentik.policies.types import PolicyRequest

FACT_OAUTH_AUTHORIZE = "oauth_authorize"

registry.fact(
    FACT_OAUTH_AUTHORIZE,
    _("OAuth2 authorization request"),
    _("Parameters of an OAuth2/OpenID Connect authorization request to an application."),
)
registry.target("authentik_core.application", [FACT_OAUTH_AUTHORIZE])
_OAUTH = [FACT_OAUTH_AUTHORIZE]


@registry.variable("oauth.scopes", _("Requested scopes"), T.list(T.STRING), requires=_OAUTH)
def oauth_scopes(request: PolicyRequest):
    scopes = request.context.get("oauth_scopes")
    return sorted(scopes) if scopes is not None else MISSING


@registry.variable("oauth.grant_type", _("Grant type"), T.STRING, requires=_OAUTH)
def oauth_grant_type(request: PolicyRequest):
    return request.context.get("oauth_grant_type", MISSING)


@registry.variable("oauth.response_type", _("Response type"), T.STRING, requires=_OAUTH)
def oauth_response_type(request: PolicyRequest):
    return request.context.get("oauth_response_type", MISSING)


@registry.variable("oauth.redirect_uri", _("Redirect URI"), T.STRING, requires=_OAUTH)
def oauth_redirect_uri(request: PolicyRequest):
    return request.context.get("oauth_redirect_uri", MISSING)
