from django.urls import path

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
    path("psso/token/", TokenView.as_view(), name="token"),
]

api_urlpatterns = [
    path(
        "endpoints/agent/psso/register/device/",
        RegisterDeviceView.as_view(),
        name="register-device",
    ),
    path("endpoints/agent/psso/register/user/", RegisterUserView.as_view(), name="register-user"),
]
