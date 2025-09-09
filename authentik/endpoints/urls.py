from authentik.endpoints.api.devices import DeviceViewSet

api_urlpatterns = [
    ("endpoints/devices", DeviceViewSet, "endpoint_device"),
]
