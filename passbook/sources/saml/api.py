"""SAMLSource API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.admin.forms.source import SOURCE_FORM_FIELDS
from passbook.sources.saml.models import SAMLSource


class SAMLSourceSerializer(ModelSerializer):
    """SAMLSource Serializer"""

    class Meta:

        model = SAMLSource
        fields = SOURCE_FORM_FIELDS + [
            "issuer",
            "sso_url",
            "name_id_policy",
            "binding_type",
            "slo_url",
            "temporary_user_delete_after",
            "signing_kp",
        ]


class SAMLSourceViewSet(ModelViewSet):
    """SAMLSource Viewset"""

    queryset = SAMLSource.objects.all()
    serializer_class = SAMLSourceSerializer
