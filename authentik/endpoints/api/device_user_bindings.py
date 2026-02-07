from authentik.endpoints.api.connectors import ConnectorSerializer
from authentik.endpoints.models import DeviceUserBinding
from authentik.policies.api.bindings import PolicyBindingSerializer, PolicyBindingViewSet


class DeviceUserBindingSerializer(PolicyBindingSerializer):

    connector_obj = ConnectorSerializer(source="connector", read_only=True)

    class Meta:
        model = DeviceUserBinding
        fields = PolicyBindingSerializer.Meta.fields + [
            "is_primary",
            "connector",
            "connector_obj",
        ]
        extra_kwargs = {"connector": {"read_only": True}}


class DeviceUserBindingViewSet(PolicyBindingViewSet):
    """PolicyBinding Viewset"""

    serializer_class = DeviceUserBindingSerializer
    queryset = (
        DeviceUserBinding.objects.all()
        .select_related("target", "group", "user")
        .prefetch_related("policy")
    )  # prefetching policy so we resolve the subclass
