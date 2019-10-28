"""ApplicationGatewayProvider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.providers.app_gw.models import ApplicationGatewayProvider


class ApplicationGatewayProviderSerializer(ModelSerializer):
    """ApplicationGatewayProvider Serializer"""

    class Meta:

        model = ApplicationGatewayProvider
        fields = ['pk', 'server_name', 'upstream', 'enabled', 'authentication_header',
                  'default_content_type', 'upstream_ssl_verification', 'property_mappings']

class ApplicationGatewayProviderViewSet(ModelViewSet):
    """ApplicationGatewayProvider Viewset"""

    queryset = ApplicationGatewayProvider.objects.all()
    serializer_class = ApplicationGatewayProviderSerializer
