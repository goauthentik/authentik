from rest_framework.viewsets import ModelViewSet

from authentik.core.api.sources import SourceSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.sources.telegram.models import TelegramSource


class TelegramSourceSerializer(SourceSerializer):
    class Meta:
        model = TelegramSource
        fields = SourceSerializer.Meta.fields + [
            'bot_username',
            'bot_token',
            'request_access']


class TelegramSourceViewSet(UsedByMixin, ModelViewSet):
    queryset = TelegramSource.objects.all()
    serializer_class = TelegramSourceSerializer
    lookup_field = 'slug'

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
        "request_access",
    ]
    search_fields = ["name", "slug"]
    ordering = ["name"]
