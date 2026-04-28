from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.telegram.api.source_connection import UserTelegramSourceConnectionSerializer
from authentik.sources.telegram.models import TelegramSource, UserTelegramSourceConnection
from authentik.sources.telegram.telegram import TelegramAuth


class TelegramSourceSerializer(SourceSerializer):
    class Meta:
        model = TelegramSource
        fields = SourceSerializer.Meta.fields + [
            "bot_username",
            "bot_token",
            "request_message_access",
            "pre_authentication_flow",
        ]
        extra_kwargs = {
            "bot_token": {"write_only": True},
        }


class TelegramAuthSerializer(TelegramAuth):

    def __init__(self, *args, **kwargs):
        self._bot_token = kwargs.pop("bot_token", None)
        super().__init__(*args, **kwargs)

    def get_bot_token(self):
        return self._bot_token


class TelegramSourceViewSet(UsedByMixin, ModelViewSet):
    queryset = TelegramSource.objects.all()
    serializer_class = TelegramSourceSerializer
    lookup_field = "slug"

    filterset_fields = [
        "pbm_uuid",
        "name",
        "slug",
        "enabled",
        "authentication_flow",
        "enrollment_flow",
        "policy_engine_mode",
        "user_matching_mode",
        "group_matching_mode",
        "bot_username",
        "request_message_access",
    ]
    search_fields = ["name", "slug"]
    ordering = ["name"]

    @extend_schema(
        request=TelegramAuthSerializer,
        responses={
            201: UserTelegramSourceConnectionSerializer,
            403: OpenApiResponse(description="Access denied"),
        },
    )
    @action(
        methods=["POST"],
        url_path="connect_user",
        detail=True,
        pagination_class=None,
        filter_backends=[],
        permission_classes=[IsAuthenticated],
    )
    def connect_user(self, request: Request, slug: str) -> Response:

        source: TelegramSource = get_object_or_404(TelegramSource, slug=slug)
        serializer = TelegramAuthSerializer(bot_token=source.bot_token, data=request.data)
        serializer.is_valid(raise_exception=True)

        connection, created = UserTelegramSourceConnection.objects.get_or_create(
            source=source,
            identifier=serializer.validated_data["id"],
            defaults={"user": request.user},
        )
        if not created and connection.user != request.user:
            return Response(
                data={"detail": _("This Telegram account is already connected to another user.")},
                status=403,
            )
        return Response(
            data=UserTelegramSourceConnectionSerializer(instance=connection).data, status=201
        )
