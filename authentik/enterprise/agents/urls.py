from authentik.enterprise.agents.api import AgentViewSet

api_urlpatterns = [
    ("agents/agents", AgentViewSet),
]
