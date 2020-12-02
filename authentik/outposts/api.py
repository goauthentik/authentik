"""Outpost API Views"""
from rest_framework.serializers import JSONField, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    Outpost,
)


class OutpostSerializer(ModelSerializer):
    """Outpost Serializer"""

    _config = JSONField()

    class Meta:

        model = Outpost
        fields = ["pk", "name", "providers", "service_connection", "_config"]


class OutpostViewSet(ModelViewSet):
    """Outpost Viewset"""

    queryset = Outpost.objects.all()
    serializer_class = OutpostSerializer


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
