"""ProxyProvider API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from passbook.providers.proxy.models import ProxyProvider


class ProxyProviderSerializer(ModelSerializer):
    """ProxyProvider Serializer"""

    def create(self, validated_data):
        instance: ProxyProvider = super().create(validated_data)
        instance.set_oauth_defaults()
        instance.save()
        return instance

    def update(self, instance: ProxyProvider, validated_data):
        instance.set_oauth_defaults()
        return super().update(instance, validated_data)

    class Meta:

        model = ProxyProvider
        fields = ["pk", "name", "internal_host", "external_host"]


class ProxyProviderViewSet(ModelViewSet):
    """ProxyProvider Viewset"""

    queryset = ProxyProvider.objects.all()
    serializer_class = ProxyProviderSerializer
