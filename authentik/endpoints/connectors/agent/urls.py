from django.urls import path

from authentik.endpoints.connectors.agent.api.connector import AgentConnectorViewSet
from authentik.endpoints.connectors.agent.views.apple_ssoext import SSOExtensionView

api_urlpatterns = [("endpoints/agents/connectors", AgentConnectorViewSet)]

urlpatterns = [path("apple_ssoext/", SSOExtensionView.as_view(), name="apple-ssoext")]
