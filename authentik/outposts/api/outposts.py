"""Outpost API Views"""
from django.db.models import Model
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import BooleanField, CharField, DateTimeField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import JSONField, ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.providers import ProviderSerializer
from authentik.outposts.models import Outpost


class OutpostSerializer(ModelSerializer):
    """Outpost Serializer"""

    _config = JSONField()
    providers = ProviderSerializer(many=True, read_only=True)

    class Meta:

        model = Outpost
        fields = [
            "pk",
            "name",
            "providers",
            "service_connection",
            "token_identifier",
            "_config",
        ]


class OutpostHealthSerializer(Serializer):
    """Outpost health status"""

    last_seen = DateTimeField(read_only=True)
    version = CharField(read_only=True)
    version_should = CharField(read_only=True)
    version_outdated = BooleanField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class OutpostViewSet(ModelViewSet):
    """Outpost Viewset"""

    queryset = Outpost.objects.all()
    serializer_class = OutpostSerializer

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
