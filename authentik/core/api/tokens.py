"""Tokens API Viewset"""
from django.db.models.base import Model
from django.http.response import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.users import UserSerializer
from authentik.core.models import Token
from authentik.events.models import Event, EventAction


class TokenSerializer(ModelSerializer):
    """Token Serializer"""

    user = UserSerializer()

    class Meta:

        model = Token
        fields = [
            "pk",
            "identifier",
            "intent",
            "user",
            "description",
            "expires",
            "expiring",
        ]
        depth = 2


class TokenViewSerializer(Serializer):
    """Show token's current key"""

    key = CharField(read_only=True)

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class TokenViewSet(ModelViewSet):
    """Token Viewset"""

    lookup_field = "identifier"
    queryset = Token.filter_not_expired()
    serializer_class = TokenSerializer
    search_fields = [
        "identifier",
        "intent",
        "user__username",
        "description",
    ]
    filterset_fields = [
        "identifier",
        "intent",
        "user__username",
        "description",
    ]
    ordering = ["expires"]

    @swagger_auto_schema(responses={200: TokenViewSerializer(many=False)})
    @action(detail=True)
    # pylint: disable=unused-argument
    def view_key(self, request: Request, identifier: str) -> Response:
        """Return token key and log access"""
        token: Token = self.get_object()
        if token.is_expired:
            raise Http404
        Event.new(EventAction.SECRET_VIEW, secret=token).from_http(  # noqa # nosec
            request
        )
        return Response(TokenViewSerializer({"key": token.key}).data)
