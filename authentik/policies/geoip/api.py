"""GeoIP Policy API Views"""

from django_countries.serializer_fields import CountryField
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.geoip.models import GeoIPPolicy

COUNTRY_SCHEMA = {
    "code": CountryField(),
    "name": serializers.CharField(),
}


@extend_schema_field(
    inline_serializer(
        "DetailedCountrySerializer",
        COUNTRY_SCHEMA,
    )
)
class DetailedCountryField(CountryField):
    def __init__(self):
        super().__init__(country_dict=True)


class GeoIPPolicySerializer(PolicySerializer):
    """GeoIP Policy Serializer"""

    countries = serializers.ListField(child=DetailedCountryField())

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
