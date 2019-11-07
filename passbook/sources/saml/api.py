"""SAMLSource API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.sources.saml.models import SAMLSource


class SAMLSourceSerializer(ModelSerializer):
    """SAMLSource Serializer"""

    class Meta:

        model = SAMLSource
        fields = ['pk', 'entity_id', 'idp_url', 'idp_logout_url', 'auto_logout', 'signing_cert']


class SAMLSourceViewSet(ModelViewSet):
    """SAMLSource Viewset"""

    queryset = SAMLSource.objects.all()
    serializer_class = SAMLSourceSerializer
