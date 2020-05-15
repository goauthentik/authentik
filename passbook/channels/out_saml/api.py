"""SAMLOutlet API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.channels.out_saml.models import SAMLOutlet, SAMLPropertyMapping


class SAMLOutletSerializer(ModelSerializer):
    """SAMLOutlet Serializer"""

    class Meta:

        model = SAMLOutlet
        fields = [
            "pk",
            "name",
            "processor_path",
            "acs_url",
            "audience",
            "issuer",
            "assertion_valid_not_before",
            "assertion_valid_not_on_or_after",
            "session_valid_not_on_or_after",
            "property_mappings",
            "digest_algorithm",
            "signature_algorithm",
            "signing_kp",
            "require_signing",
        ]


class SAMLOutletViewSet(ModelViewSet):
    """SAMLOutlet Viewset"""

    queryset = SAMLOutlet.objects.all()
    serializer_class = SAMLOutletSerializer


class SAMLPropertyMappingSerializer(ModelSerializer):
    """SAMLPropertyMapping Serializer"""

    class Meta:

        model = SAMLPropertyMapping
        fields = ["pk", "name", "saml_name", "friendly_name", "expression"]


class SAMLPropertyMappingViewSet(ModelViewSet):
    """SAMLPropertyMapping Viewset"""

    queryset = SAMLPropertyMapping.objects.all()
    serializer_class = SAMLPropertyMappingSerializer
