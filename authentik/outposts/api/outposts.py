"""Outpost API Views"""
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, DateTimeField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import JSONField, ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.outposts.models import Outpost, default_outpost_config


class OutpostSerializer(ModelSerializer):
    """Outpost Serializer"""

    _config = JSONField()
    providers_obj = ProviderSerializer(source="providers", many=True, read_only=True)

    class Meta:

        model = Outpost
        fields = [
            "pk",
            "name",
            "providers",
            "providers_obj",
            "service_connection",
            "token_identifier",
            "_config",
        ]


class OutpostDefaultConfigSerializer(PassiveSerializer):
    """Global default outpost config"""

    config = JSONField(read_only=True)


class OutpostHealthSerializer(PassiveSerializer):
    """Outpost health status"""

    last_seen = DateTimeField(read_only=True)
    version = CharField(read_only=True)
    version_should = CharField(read_only=True)
    version_outdated = BooleanField(read_only=True)


class OutpostViewSet(ModelViewSet):
    """Outpost Viewset"""

    queryset = Outpost.objects.all()
    serializer_class = OutpostSerializer
    filterset_fields = {
        "providers": ["isnull"],
    }
    search_fields = [
        "name",
        "providers__name",
    ]
    ordering = ["name"]

    @swagger_auto_schema(responses={200: OutpostHealthSerializer(many=True)})
    @action(methods=["GET"], detail=True)
    # pylint: disable=invalid-name, unused-argument
    def health(self, request: Request, pk: int) -> Response:
        """Get outposts current health"""
        outpost: Outpost = self.get_object()
        states = []
        for state in outpost.state:
            states.append(
                {
                    "last_seen": state.last_seen,
                    "version": state.version,
                    "version_should": state.version_should,
                    "version_outdated": state.version_outdated,
                }
            )
        return Response(OutpostHealthSerializer(states, many=True).data)

    @swagger_auto_schema(responses={200: OutpostDefaultConfigSerializer(many=False)})
    @action(detail=False, methods=["GET"])
    def default_settings(self, request: Request) -> Response:
        """Global default outpost config"""
        host = self.request.build_absolute_uri("/")
        return Response({"config": default_outpost_config(host)})
