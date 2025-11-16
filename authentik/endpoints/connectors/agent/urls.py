from django.urls import path

from authentik.endpoints.connectors.agent.api.connector import AgentConnectorViewSet
from authentik.endpoints.connectors.agent.api.enrollment_tokens import EnrollmentTokenViewSet
from authentik.endpoints.connectors.agent.views.apple_ssoext import SSOExtensionView

api_urlpatterns = [
    ("endpoints/agents/connectors", AgentConnectorViewSet),
    ("endpoints/agents/enrollment_tokens", EnrollmentTokenViewSet),
]

urlpatterns = [path("apple_ssoext/", SSOExtensionView.as_view(), name="apple-ssoext")]
