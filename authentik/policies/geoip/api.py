"""GeoIP Policy API Views"""

from django_countries import countries
from django_countries.serializer_fields import CountryField
from django_countries.serializers import CountryFieldMixin
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.policies.api.policies import PolicySerializer
from authentik.policies.geoip.models import GeoIPPolicy
from authentik.policies.geoip.serializer_fields import DetailedCountryField


class DetailedCountrySerializer(serializers.Serializer):
    code = CountryField()
    name = serializers.CharField()


class ISO3166View(ListAPIView):
    """Get all countries in ISO-3166-1"""

    permission_classes = [AllowAny]
    queryset = [{"code": code, "name": name} for (code, name) in countries]
    serializer_class = DetailedCountrySerializer
    filter_backends = []
    pagination_class = None


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
            "check_history",
            "history_max_distance_km",
            "distance_tolerance_km",
            "history_login_count",
        ]


class GeoIPPolicyViewSet(UsedByMixin, ModelViewSet):
    """GeoIP Viewset"""

    queryset = GeoIPPolicy.objects.all()
    serializer_class = GeoIPPolicySerializer
    filterset_fields = ["name"]
    ordering = ["name"]
    search_fields = ["name"]
