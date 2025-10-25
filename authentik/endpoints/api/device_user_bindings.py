

from authentik.endpoints.models import DeviceUserBinding
from authentik.policies.api.bindings import PolicyBindingSerializer, PolicyBindingViewSet


class DeviceUserBindingSerializer(PolicyBindingSerializer):

    class Meta:
        model = DeviceUserBinding
        fields = PolicyBindingSerializer.Meta.fields + [
            "is_primary",
        ]


class DeviceUserBindingViewSet(PolicyBindingViewSet):
    """PolicyBinding Viewset"""

    queryset = (
        DeviceUserBinding.objects.all()
        .select_related("target", "group", "user")
        .prefetch_related("policy")
    )  # prefetching policy so we resolve the subclass
