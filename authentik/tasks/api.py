from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.events.logs import LogEventSerializer
from authentik.tasks.models import Task
from authentik.tenants.utils import get_current_tenant


class TaskSerializer(ModelSerializer):
    messages = LogEventSerializer(many=True, source="_messages")

    class Meta:
        model = Task
        fields = [
            "message_id",
            "queue_name",
            "actor_name",
            "state",
            "mtime",
            "rel_obj_content_type",
            "rel_obj_id",
            "uid",
            "messages",
            "aggregated_status",
        ]


class TaskViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    queryset = Task.objects.none()
    serializer_class = TaskSerializer
    search_fields = (
        "message_id",
        "queue_name",
        "actor_name",
        "state",
        "_uid",
        "aggregated_status",
    )
    filterset_fields = (
        "queue_name",
        "actor_name",
        "state",
        "aggregated_status",
    )
    ordering = ("-mtime",)

    def get_queryset(self):
        return Task.objects.filter(tenant=get_current_tenant())
