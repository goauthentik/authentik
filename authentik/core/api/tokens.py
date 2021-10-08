"""Tokens API Viewset"""
from typing import Any

from django.http.response import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema
from guardian.shortcuts import get_anonymous_user
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ModelViewSet

from authentik.api.authorization import OwnerSuperuserPermissions
from authentik.api.decorators import permission_required
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import USER_ATTRIBUTE_TOKEN_EXPIRING, Token, TokenIntents
from authentik.events.models import Event, EventAction
from authentik.managed.api import ManagedSerializer


class TokenSerializer(ManagedSerializer, ModelSerializer):
    """Token Serializer"""

    user_obj = UserSerializer(required=False, source="user")

    def validate(self, attrs: dict[Any, str]) -> dict[Any, str]:
        """Ensure only API or App password tokens are created."""
        request: Request = self.context["request"]
        attrs.setdefault("user", request.user)
        attrs.setdefault("intent", TokenIntents.INTENT_API)
        if attrs.get("intent") not in [TokenIntents.INTENT_API, TokenIntents.INTENT_APP_PASSWORD]:
            raise ValidationError(f"Invalid intent {attrs.get('intent')}")
        return attrs

    class Meta:

        model = Token
        fields = [
            "pk",
            "managed",
            "identifier",
            "intent",
            "user",
            "user_obj",
            "description",
            "expires",
            "expiring",
        ]
        extra_kwargs = {
            "user": {"required": False},
        }


class TokenViewSerializer(PassiveSerializer):
    """Show token's current key"""

    key = CharField(read_only=True)


class TokenViewSet(UsedByMixin, ModelViewSet):
    """Token Viewset"""

    lookup_field = "identifier"
    queryset = Token.objects.all()
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
        "expires",
        "expiring",
        "managed",
    ]
    ordering = ["identifier", "expires"]
    permission_classes = [OwnerSuperuserPermissions]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)

    def perform_create(self, serializer: TokenSerializer):
        if not self.request.user.is_superuser:
            return serializer.save(
                user=self.request.user,
                expiring=self.request.user.attributes.get(USER_ATTRIBUTE_TOKEN_EXPIRING, True),
            )
        return super().perform_create(serializer)

    @permission_required("authentik_core.view_token_key")
    @extend_schema(
        responses={
            200: TokenViewSerializer(many=False),
            404: OpenApiResponse(description="Token not found or expired"),
        }
    )
    @action(detail=True, pagination_class=None, filter_backends=[])
    # pylint: disable=unused-argument
    def view_key(self, request: Request, identifier: str) -> Response:
        """Return token key and log access"""
        token: Token = self.get_object()
        if token.is_expired:
            raise Http404
        Event.new(EventAction.SECRET_VIEW, secret=token).from_http(request)  # noqa # nosec
        return Response(TokenViewSerializer({"key": token.key}).data)
