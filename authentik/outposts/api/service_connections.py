"""Outpost API Views"""
from dataclasses import asdict

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from kubernetes.client.configuration import Configuration
from kubernetes.config.config_exception import ConfigException
from kubernetes.config.kube_config import load_kube_config_from_dict
from rest_framework import mixins, serializers
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, ReadOnlyField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import MetaNameSerializer, PassiveSerializer, TypeCreateSerializer
from authentik.lib.utils.reflection import all_subclasses
from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    OutpostServiceConnection,
)


class ServiceConnectionSerializer(ModelSerializer, MetaNameSerializer):
    """ServiceConnection Serializer"""

    component = ReadOnlyField()

    def get_component(self, obj: OutpostServiceConnection) -> str:
        """Get object type so that we know how to edit the object"""
        # pyright: reportGeneralTypeIssues=false
        if obj.__class__ == OutpostServiceConnection:
            return ""
        return obj.component

    class Meta:

        model = OutpostServiceConnection
        fields = [
            "pk",
            "name",
            "local",
            "component",
            "verbose_name",
            "verbose_name_plural",
            "meta_model_name",
        ]


class ServiceConnectionStateSerializer(PassiveSerializer):
    """Serializer for Service connection state"""

    healthy = BooleanField(read_only=True)
    version = CharField(read_only=True)


class ServiceConnectionViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """ServiceConnection Viewset"""

    queryset = OutpostServiceConnection.objects.select_subclasses()
    serializer_class = ServiceConnectionSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]

    @extend_schema(responses={200: TypeCreateSerializer(many=True)})
    @action(detail=False, pagination_class=None, filter_backends=[])
    def types(self, request: Request) -> Response:
        """Get all creatable service connection types"""
        data = []
        for subclass in all_subclasses(self.queryset.model):
            subclass: OutpostServiceConnection
            # pyright: reportGeneralTypeIssues=false
            data.append(
                {
                    "name": subclass._meta.verbose_name,
                    "description": subclass.__doc__,
                    "component": subclass().component,
                    "model_name": subclass._meta.model_name,
                }
            )
        return Response(TypeCreateSerializer(data, many=True).data)

    @extend_schema(responses={200: ServiceConnectionStateSerializer(many=False)})
    @action(detail=True, pagination_class=None, filter_backends=[])
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


class DockerServiceConnectionViewSet(UsedByMixin, ModelViewSet):
    """DockerServiceConnection Viewset"""

    queryset = DockerServiceConnection.objects.all()
    serializer_class = DockerServiceConnectionSerializer
    filterset_fields = ["name", "local", "url", "tls_verification", "tls_authentication"]
    ordering = ["name"]
    search_fields = ["name"]


class KubernetesServiceConnectionSerializer(ServiceConnectionSerializer):
    """KubernetesServiceConnection Serializer"""

    def validate_kubeconfig(self, kubeconfig):
        """Validate kubeconfig by attempting to load it"""
        if kubeconfig == {}:
            if not self.initial_data["local"]:
                raise serializers.ValidationError(
                    _("You can only use an empty kubeconfig when connecting to a local cluster.")
                )
            # Empty kubeconfig is valid
            return kubeconfig
        config = Configuration()
        try:
            load_kube_config_from_dict(kubeconfig, client_configuration=config)
        except ConfigException:
            raise serializers.ValidationError(_("Invalid kubeconfig"))
        return kubeconfig

    class Meta:

        model = KubernetesServiceConnection
        fields = ServiceConnectionSerializer.Meta.fields + ["kubeconfig"]


class KubernetesServiceConnectionViewSet(UsedByMixin, ModelViewSet):
    """KubernetesServiceConnection Viewset"""

    queryset = KubernetesServiceConnection.objects.all()
    serializer_class = KubernetesServiceConnectionSerializer
    filterset_fields = ["name", "local"]
    ordering = ["name"]
    search_fields = ["name"]
