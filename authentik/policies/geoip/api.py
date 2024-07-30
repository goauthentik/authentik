"""GeoIP Policy API Views"""

from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.geoip.models import GeoIPPolicy
from authentik.policies.geoip.serializer_fields import DetailedCountryField


class GeoIPPolicySerializer(CountryFieldMixin, PolicySerializer):
    """GeoIP Policy Serializer"""

    countries_obj = serializers.ListField(
        child=DetailedCountryField(), source="countries", read_only=True
    )

    class Meta:
        model = GeoIPPolicy
        fields = PolicySerializer.Meta.fields + [
            "asns",
            "countries",
            "countries_obj",
        ]


class GeoIPPolicyViewSet(UsedByMixin, ModelViewSet):
    """GeoIP Viewset"""

    queryset = GeoIPPolicy.objects.all()
    serializer_class = GeoIPPolicySerializer
    filterset_fields = ["name"]
    ordering = ["name"]
    search_fields = ["name"]
