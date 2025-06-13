from rest_framework.viewsets import ModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.core.models import File

LOGGER = get_logger()


class FileSerializer(ModelSerializer):
    class Meta:
        model = File
        fields = (
            "pk",
            "name",
            "content",
            "private",
        )


class FileViewSet(UsedByMixin, ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    filterset_fields = ("private",)
    ordering = ("name",)
    search_fields = ("name",)
