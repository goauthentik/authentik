"""Outpost API Views"""
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    OutpostServiceConnection,
)


class ServiceConnectionSerializer(ModelSerializer):
    """ServiceConnection Serializer"""

    class Meta:

        model = OutpostServiceConnection
        fields = ["pk", "name"]


class ServiceConnectionViewSet(ModelViewSet):
    """ServiceConnection Viewset"""

    queryset = OutpostServiceConnection.objects.all()
    serializer_class = ServiceConnectionSerializer


class DockerServiceConnectionSerializer(ModelSerializer):
    """DockerServiceConnection Serializer"""

    class Meta:

        model = DockerServiceConnection
        fields = [
            "pk",
            "name",
            "local",
            "url",
            "tls_verification",
            "tls_authentication",
        ]


class DockerServiceConnectionViewSet(ModelViewSet):
    """DockerServiceConnection Viewset"""

    queryset = DockerServiceConnection.objects.all()
    serializer_class = DockerServiceConnectionSerializer


class KubernetesServiceConnectionSerializer(ModelSerializer):
    """KubernetesServiceConnection Serializer"""

    class Meta:

        model = KubernetesServiceConnection
        fields = ["pk", "name", "local", "kubeconfig"]


class KubernetesServiceConnectionViewSet(ModelViewSet):
    """KubernetesServiceConnection Viewset"""

    queryset = KubernetesServiceConnection.objects.all()
    serializer_class = KubernetesServiceConnectionSerializer
