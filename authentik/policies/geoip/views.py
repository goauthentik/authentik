from django_countries import countries
from django_countries.serializer_fields import CountryField
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny


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
