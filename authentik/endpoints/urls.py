from authentik.endpoints.api.connectors import ConnectorViewSet
from authentik.endpoints.api.device_group import DeviceGroupViewSet
from authentik.endpoints.api.devices import DeviceViewSet

api_urlpatterns = [
    ("endpoints/connectors", ConnectorViewSet, "endpoint_connectors"),
    ("endpoints/devices", DeviceViewSet, "endpoint_device"),
    ("endpoints/device_groups", DeviceGroupViewSet, "endpoint_device_groups"),
]
