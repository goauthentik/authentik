from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet

from authentik.core.api.utils import ModelSerializer
from authentik.tasks.models import Task
from authentik.tasks.schedules.models import Schedule
from authentik.tenants.utils import get_current_tenant


class TaskSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "message_id",
            "queue_name",
            "actor_name",
            "state",
            "mtime",
            "schedule_uid",
            "uid",
        ]


class TaskViewSet(
    RetrieveModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    serializer_class = TaskSerializer
    search_fields = (
        "message_id",
        "queue_name",
        "actor_name",
        "state",
        "schedule_uid",
    )
    filterset_fields = (
        "queue_name",
        "actor_name",
        "state",
        "schedule_uid",
    )
    ordering = (
        "actor_name",
        "-mtime",
    )

    def get_queryset(self):
        qs = Task.objects.filter(tenant=get_current_tenant())
        if self.request.query_params.get("exclude_scheduled", "false").lower() == "true":
            qs = qs.exclude(schedule_uid__in=Schedule.objects.all().values_list("uid", flat=True))
        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter("exclude_scheduled", bool, default=False),
        ]
    )
    def list(self, *args, **kwargs):
        return super().list(*args, **kwargs)
