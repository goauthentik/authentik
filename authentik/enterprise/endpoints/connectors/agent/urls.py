from django.urls import path

from authentik.enterprise.endpoints.connectors.agent.views.apple_jwks import AppleJWKSView
from authentik.enterprise.endpoints.connectors.agent.views.apple_nonce import NonceView
from authentik.enterprise.endpoints.connectors.agent.views.apple_register import (
    RegisterDeviceView,
    RegisterUserView,
)
from authentik.enterprise.endpoints.connectors.agent.views.apple_token import TokenView
from authentik.enterprise.endpoints.connectors.agent.views.auth_interactive import (
    AgentInteractiveAuth,
)

urlpatterns = [
    path(
        "authenticate/<uuid:token_uuid>/",
        AgentInteractiveAuth.as_view(),
        name="authenticate",
    ),
    path("psso/token/", TokenView.as_view(), name="psso-token"),
    path("psso/jwks/", AppleJWKSView.as_view(), name="psso-jwks"),
    path("psso/nonce/", NonceView.as_view(), name="psso-nonce"),
]

api_urlpatterns = [
    path(
        "endpoints/agents/psso/register/device/",
        RegisterDeviceView.as_view(),
        name="psso-register-device",
    ),
    path(
        "endpoints/agents/psso/register/user/",
        RegisterUserView.as_view(),
        name="psso-register-user",
    ),
]
