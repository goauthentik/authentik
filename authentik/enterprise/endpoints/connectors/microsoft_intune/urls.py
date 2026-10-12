from authentik.enterprise.endpoints.connectors.microsoft_intune.api import (
    MicrosoftIntuneConnectorViewSet,
)

api_urlpatterns = [("endpoints/microsoft_intune/connectors", MicrosoftIntuneConnectorViewSet)]
