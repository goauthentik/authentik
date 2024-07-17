from django_countries import countries
from django_countries.serializer_fields import CountryField
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

COUNTRY_SCHEMA = {
    "code": CountryField(),
    "name": serializers.CharField(),
}


class ISO3166View(APIView):
    """Get all countries in ISO-3166-1"""

    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            200: inline_serializer(
                "DetailedCountryListSerializer",
                COUNTRY_SCHEMA,
                many=True,
            )
        },
    )
    def get(self, request: Request) -> Response:
        """Get all countries in ISO-3166-1"""
        country_list = [{"code": code, "name": name} for (code, name) in countries]
        return Response(country_list)
