from authentik.endpoints.connectors.agent.api.connector import AgentConnectorViewSet
from authentik.endpoints.connectors.agent.api.enrollment_tokens import EnrollmentTokenViewSet

api_urlpatterns = [
    ("endpoints/agents/connectors", AgentConnectorViewSet),
    ("endpoints/agents/enrollment_tokens", EnrollmentTokenViewSet),
]
