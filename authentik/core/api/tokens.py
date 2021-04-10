"""Tokens API Viewset"""
from django.http.response import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.decorators import permission_required
from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import Token
from authentik.events.models import Event, EventAction
from authentik.managed.api import ManagedSerializer


class TokenSerializer(ManagedSerializer, ModelSerializer):
    """Token Serializer"""

    user = UserSerializer(required=False)

    class Meta:

        model = Token
        fields = [
            "pk",
            "managed",
            "identifier",
            "intent",
            "user",
            "description",
            "expires",
            "expiring",
        ]
        depth = 2


class TokenViewSerializer(PassiveSerializer):
    """Show token's current key"""

    key = CharField(read_only=True)


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

    def perform_create(self, serializer: TokenSerializer):
        serializer.save(user=self.request.user)

    @permission_required("authentik_core.view_token_key")
    @swagger_auto_schema(
        responses={
            200: TokenViewSerializer(many=False),
            404: "Token not found or expired",
        }
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
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
