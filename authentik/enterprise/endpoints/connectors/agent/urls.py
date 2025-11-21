from django.urls import path

from authentik.enterprise.endpoints.connectors.agent.views.auth_interactive import (
    AgentInteractiveAuth,
)

urlpatterns = [
    path(
        "authenticate/<uuid:token_uuid>/",
        AgentInteractiveAuth.as_view(),
        name="authenticate",
    ),
]
