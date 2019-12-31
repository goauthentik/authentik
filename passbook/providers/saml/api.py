"""SAMLProvider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.providers.saml.models import SAMLPropertyMapping, SAMLProvider


class SAMLProviderSerializer(ModelSerializer):
    """SAMLProvider Serializer"""

    class Meta:

        model = SAMLProvider
        fields = [
            "pk",
            "name",
            "property_mappings",
            "acs_url",
            "audience",
            "processor_path",
            "issuer",
            "assertion_valid_for",
            "signing",
            "signing_cert",
            "signing_key",
        ]


class SAMLProviderViewSet(ModelViewSet):
    """SAMLProvider Viewset"""

    queryset = SAMLProvider.objects.all()
    serializer_class = SAMLProviderSerializer


class SAMLPropertyMappingSerializer(ModelSerializer):
    """SAMLPropertyMapping Serializer"""

    class Meta:

        model = SAMLPropertyMapping
        fields = ["pk", "name", "saml_name", "friendly_name", "values"]


class SAMLPropertyMappingViewSet(ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
