"""Policy variables provided by the OAuth2 provider"""

from django.utils.translation import gettext_lazy as _

from authentik.policies.conditional.registry import KnownParam, ParamKind, registry
from authentik.policies.conditional.types import MISSING, T, dig
from authentik.policies.types import PolicyRequest

FACT_OAUTH_AUTHORIZE = "oauth_authorize"

registry.fact(
    FACT_OAUTH_AUTHORIZE,
    _("OAuth2 authorization request"),
    _("Parameters of an OAuth2/OpenID Connect authorization request to an application."),
)
FACT_OAUTH_TOKEN = "oauth_token"

registry.fact(
    FACT_OAUTH_TOKEN,
    _("OAuth2 token request"),
    _(
        "Parameters of an OAuth2 token request to an application, for example with the "
        "client credentials or token exchange grant."
    ),
)
registry.target("authentik_core.application", [FACT_OAUTH_AUTHORIZE, FACT_OAUTH_TOKEN])
_OAUTH = [FACT_OAUTH_AUTHORIZE, FACT_OAUTH_TOKEN]


@registry.variable("oauth.scopes", _("Requested scopes"), T.list(T.STRING), requires=_OAUTH)
def oauth_scopes(request: PolicyRequest):
    scopes = request.context.get("oauth_scopes")
    return sorted(scopes) if scopes is not None else MISSING


@registry.variable("oauth.grant_type", _("Grant type"), T.STRING, requires=_OAUTH)
def oauth_grant_type(request: PolicyRequest):
    return request.context.get("oauth_grant_type", MISSING)


@registry.variable(
    "oauth.response_type", _("Response type"), T.STRING, requires=[FACT_OAUTH_AUTHORIZE]
)
def oauth_response_type(request: PolicyRequest):
    return request.context.get("oauth_response_type", MISSING)


@registry.variable(
    "oauth.redirect_uri", _("Redirect URI"), T.STRING, requires=[FACT_OAUTH_AUTHORIZE]
)
def oauth_redirect_uri(request: PolicyRequest):
    return request.context.get("oauth_redirect_uri", MISSING)


@registry.variable(
    "oauth.jwt",
    _("Federated JWT claim"),
    T.ANY,
    requires=[FACT_OAUTH_TOKEN],
    param=ParamKind.PATH,
    params=[
        KnownParam("iss", _("Issuer"), T.STRING),
        KnownParam("sub", _("Subject"), T.STRING),
        KnownParam("azp", _("Authorized party"), T.STRING),
        KnownParam("email", _("Email"), T.STRING),
        KnownParam("iat", _("Issued at (timestamp)"), T.NUMBER),
        KnownParam("exp", _("Expires at (timestamp)"), T.NUMBER),
    ],
    description=_(
        "Claim of a JWT issued by a federated provider, used for machine-to-machine "
        "authentication, at the given dotted path."
    ),
)
def oauth_jwt(request: PolicyRequest, path: str):
    return dig(request.context.get("oauth_jwt"), path)
