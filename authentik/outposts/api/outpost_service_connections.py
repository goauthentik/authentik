"""Outpost API Views"""
from dataclasses import asdict

from django.db.models.base import Model
from django.shortcuts import reverse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.utils import MetaNameSerializer, TypeCreateSerializer
from authentik.lib.templatetags.authentik_utils import verbose_name
from authentik.lib.utils.reflection import all_subclasses
from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    OutpostServiceConnection,
)


class ServiceConnectionSerializer(ModelSerializer, MetaNameSerializer):
    """ServiceConnection Serializer"""

    object_type = SerializerMethodField()

    def get_object_type(self, obj: OutpostServiceConnection) -> str:
        """Get object type so that we know which API Endpoint to use to get the full object"""
        return obj._meta.object_name.lower().replace("serviceconnection", "")

    class Meta:

        model = OutpostServiceConnection
        fields = [
            "pk",
            "name",
            "local",
            "object_type",
            "verbose_name",
            "verbose_name_plural",
        ]


class ServiceConnectionStateSerializer(Serializer):
    """Serializer for Service connection state"""

    healthy = BooleanField(read_only=True)
    version = CharField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class ServiceConnectionViewSet(ModelViewSet):
    """ServiceConnection Viewset"""

    queryset = OutpostServiceConnection.objects.select_subclasses()
    serializer_class = ServiceConnectionSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]

    @swagger_auto_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False)
    def types(self, request: Request) -> Response:
        """Get all creatable service connection types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            data.append(
                {
                    "name": verbose_name(subclass),
                    "description": subclass.__doc__,
                    "link": reverse("authentik_admin:outpost-service-connection-create")
                    + f"?type={subclass.__name__}",
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @swagger_auto_schema(responses={200: ServiceConnectionStateSerializer(many=False)})
    @action(detail=True)
    # pylint: disable=unused-argument, invalid-name
    def state(self, request: Request, pk: str) -> Response:
        """Get the service connection's state"""
        connection = self.get_object()
        return Response(asdict(connection.state))


class DockerServiceConnectionSerializer(ServiceConnectionSerializer):
    """DockerServiceConnection Serializer"""

    class Meta:

        model = DockerServiceConnection
        fields = ServiceConnectionSerializer.Meta.fields + [
            "url",
            "tls_verification",
            "tls_authentication",
        ]


class DockerServiceConnectionViewSet(ModelViewSet):
    """DockerServiceConnection Viewset"""

    queryset = DockerServiceConnection.objects.all()
    serializer_class = DockerServiceConnectionSerializer


class KubernetesServiceConnectionSerializer(ServiceConnectionSerializer):
    """KubernetesServiceConnection Serializer"""

    class Meta:

        model = KubernetesServiceConnection
        fields = ServiceConnectionSerializer.Meta.fields + ["kubeconfig"]


class KubernetesServiceConnectionViewSet(ModelViewSet):
    """KubernetesServiceConnection Viewset"""

    queryset = KubernetesServiceConnection.objects.all()
    serializer_class = KubernetesServiceConnectionSerializer
