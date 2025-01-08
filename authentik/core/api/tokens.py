"""Tokens API Viewset"""

from typing import Any

from django.utils.timezone import now
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from guardian.shortcuts import assign_perm, get_anonymous_user
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.blueprints.api import ManagedSerializer
from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_BLUEPRINT
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.users import UserSerializer
from authentik.core.api.utils import ModelSerializer, PassiveSerializer
from authentik.core.models import (
    USER_ATTRIBUTE_TOKEN_EXPIRING,
    USER_ATTRIBUTE_TOKEN_MAXIMUM_LIFETIME,
    Token,
    TokenIntents,
    User,
    default_token_duration,
)
from authentik.events.models import Event, EventAction
from authentik.events.utils import model_to_dict
from authentik.lib.utils.time import timedelta_from_string
from authentik.rbac.decorators import permission_required


class TokenSerializer(ManagedSerializer, ModelSerializer):
    """Token Serializer"""

    user_obj = UserSerializer(required=False, source="user", read_only=True)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if SERIALIZER_CONTEXT_BLUEPRINT in self.context:
            self.fields["key"] = CharField(required=False)

    def validate_user(self, user: User):
        """Ensure user of token cannot be changed"""
        if self.instance and self.instance.user_id:
            if user.pk != self.instance.user_id:
                raise ValidationError("User cannot be changed")
        return user

    def validate(self, attrs: dict[Any, str]) -> dict[Any, str]:
        """Ensure only API or App password tokens are created."""
        request: Request = self.context.get("request")
        if not request:
            if "user" not in attrs:
                raise ValidationError("Missing user")
            if "intent" not in attrs:
                raise ValidationError("Missing intent")
        else:
            attrs.setdefault("user", request.user)
        attrs.setdefault("intent", TokenIntents.INTENT_API)
        if attrs.get("intent") not in [TokenIntents.INTENT_API, TokenIntents.INTENT_APP_PASSWORD]:
            raise ValidationError({"intent": f"Invalid intent {attrs.get('intent')}"})

        if attrs.get("intent") == TokenIntents.INTENT_APP_PASSWORD:
            # user IS in attrs
            user: User = attrs.get("user")
            max_token_lifetime = user.group_attributes(request).get(
                USER_ATTRIBUTE_TOKEN_MAXIMUM_LIFETIME,
            )
            max_token_lifetime_dt = default_token_duration()
            if max_token_lifetime is not None:
                try:
                    max_token_lifetime_dt = now() + timedelta_from_string(max_token_lifetime)
                except ValueError:
                    pass

            if "expires" in attrs and attrs.get("expires") > max_token_lifetime_dt:
                raise ValidationError(
                    {
                        "expires": (
                            f"Token expires exceeds maximum lifetime ({max_token_lifetime_dt} UTC)."
                        )
                    }
                )
        elif attrs.get("intent") == TokenIntents.INTENT_API:
            # For API tokens, expires cannot be overridden
            attrs["expires"] = default_token_duration()

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
    owner_field = "user"

    def get_queryset(self):
        user = self.request.user if self.request else get_anonymous_user()
        if user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=user.pk)

    def perform_create(self, serializer: TokenSerializer):
        if not self.request.user.is_superuser:
            instance = serializer.save(
                user=self.request.user,
                expiring=self.request.user.attributes.get(USER_ATTRIBUTE_TOKEN_EXPIRING, True),
            )
            assign_perm("authentik_core.view_token_key", self.request.user, instance)
            return instance
        return super().perform_create(serializer)

    @permission_required("authentik_core.view_token_key")
    @extend_schema(
        responses={
            200: TokenViewSerializer(many=False),
            404: OpenApiResponse(description="Token not found or expired"),
        }
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["GET"])
    def view_key(self, request: Request, identifier: str) -> Response:
        """Return token key and log access"""
        token: Token = self.get_object()
        Event.new(EventAction.SECRET_VIEW, secret=token).from_http(request)  # noqa # nosec
        return Response(TokenViewSerializer({"key": token.key}).data)

    @permission_required("authentik_core.set_token_key")
    @extend_schema(
        request=inline_serializer(
            "TokenSetKey",
            {
                "key": CharField(),
            },
        ),
        responses={
            204: OpenApiResponse(description="Successfully changed key"),
            400: OpenApiResponse(description="Missing key"),
            404: OpenApiResponse(description="Token not found or expired"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def set_key(self, request: Request, identifier: str) -> Response:
        """Set token key. Action is logged as event. `authentik_core.set_token_key` permission
        is required."""
        token: Token = self.get_object()
        key = request.data.get("key")
        if not key:
            return Response(status=400)
        token.key = key
        token.save()
        Event.new(EventAction.MODEL_UPDATED, model=model_to_dict(token)).from_http(
            request
        )  # noqa # nosec
        return Response(status=204)
