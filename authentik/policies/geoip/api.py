"""GeoIP Policy API Views"""

from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.geoip.models import GeoIPPolicy


class GeoIPPolicySerializer(PolicySerializer):
    """GeoIP Policy Serializer"""

    class Meta:
        model = GeoIPPolicy
        fields = PolicySerializer.Meta.fields + [
            "asns",
            "countries",
        ]


class GeoIPPolicyViewSet(UsedByMixin, ModelViewSet):
    """GeoIP Viewset"""

    queryset = GeoIPPolicy.objects.all()
    serializer_class = GeoIPPolicySerializer
    filterset_fields = ["name"]
    ordering = ["name"]
    search_fields = ["name"]
