"""Workaround for https://github.com/SmileyChris/django-countries/issues/441"""

from django_countries.serializer_fields import CountryField
from drf_spectacular.utils import extend_schema_field, inline_serializer
from rest_framework import serializers

DETAILED_COUNTRY_SCHEMA = {
    "code": CountryField(),
    "name": serializers.CharField(),
}


@extend_schema_field(
    inline_serializer(
        "DetailedCountryField",
        DETAILED_COUNTRY_SCHEMA,
    )
)
class DetailedCountryField(CountryField):
    def __init__(self):
        super().__init__(country_dict=True)
