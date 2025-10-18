from django.urls import path

from authentik.enterprise.endpoints.connectors.agent.api.connector import AgentConnectorViewSet
from authentik.enterprise.endpoints.connectors.agent.views.apple import SSOExtensionView

api_urlpatterns = [("endpoints/agents/connectors", AgentConnectorViewSet)]

urlpatterns = [path("apple_ssoext/", SSOExtensionView.as_view(), name="apple-ssoext")]
