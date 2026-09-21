from django.urls import path

from authentik.endpoints.connectors.agent.api.connectors import AgentConnectorViewSet
from authentik.endpoints.connectors.agent.api.enrollment_tokens import EnrollmentTokenViewSet
from authentik.endpoints.connectors.agent.views.browser_backchannel import BrowserBackchannel

urlpatterns = [
    path("browser-backchannel/", BrowserBackchannel.as_view(), name="browser-backchannel"),
]

api_urlpatterns = [
    ("endpoints/agents/connectors", AgentConnectorViewSet),
    ("endpoints/agents/enrollment_tokens", EnrollmentTokenViewSet),
]
