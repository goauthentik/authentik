"""Policy variables provided by the OAuth2 provider"""

from django.utils.translation import gettext_lazy as _

from authentik.core.policy_variables import FACT_APPLICATION
from authentik.policies.conditional.registry import (
    FACT_HTTP_REQUEST,
    KnownParam,
    ParamKind,
    context_key,
    registry,
)
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
registry.scenario(
    "oauth2_authorization",
    [FACT_HTTP_REQUEST, FACT_APPLICATION, FACT_OAUTH_AUTHORIZE],
    models=["authentik_core.application"],
    label=_("OAuth2 authorization"),
    description=_(
        "Deciding whether a user can authorize an OAuth2/OpenID Connect application, with "
        "the requested scopes."
    ),
)
registry.scenario(
    "oauth2_token",
    [FACT_HTTP_REQUEST, FACT_APPLICATION, FACT_OAUTH_TOKEN],
    models=["authentik_core.application"],
    label=_("OAuth2 machine-to-machine token"),
    description=_(
        "Deciding whether a token can be issued with the client credentials or token exchange "
        "grant."
    ),
)
_OAUTH = [FACT_OAUTH_AUTHORIZE, FACT_OAUTH_TOKEN]


@registry.variable("oauth.scopes", _("Requested scopes"), T.list(T.STRING), requires=_OAUTH)
def oauth_scopes(request: PolicyRequest):
    scopes = request.context.get("oauth_scopes")
    return sorted(scopes) if scopes is not None else MISSING


registry.add_variable(
    "oauth.grant_type", _("Grant type"), T.STRING, _OAUTH, context_key("oauth_grant_type")
)
registry.add_variable(
    "oauth.response_type",
    _("Response type"),
    T.STRING,
    [FACT_OAUTH_AUTHORIZE],
    context_key("oauth_response_type"),
)
registry.add_variable(
    "oauth.redirect_uri",
    _("Redirect URI"),
    T.STRING,
    [FACT_OAUTH_AUTHORIZE],
    context_key("oauth_redirect_uri"),
)


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
