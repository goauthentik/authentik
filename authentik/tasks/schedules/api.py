from django_filters.filters import BooleanFilter
from django_filters.filterset import FilterSet
from dramatiq.actor import Actor
from dramatiq.broker import get_broker
from dramatiq.errors import ActorNotFound
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import SerializerMethodField
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import ModelSerializer
from authentik.rbac.decorators import permission_required
from authentik.tasks.models import Task, TaskStatus
from authentik.tasks.schedules.models import Schedule

LOGGER = get_logger()


class ScheduleSerializer(ModelSerializer):
    rel_obj_app_label = ReadOnlyField(source="rel_obj_content_type.app_label")
    rel_obj_model = ReadOnlyField(source="rel_obj_content_type.model")

    description = SerializerMethodField()
    last_task_status = SerializerMethodField()

    class Meta:
        model = Schedule
        fields = (
            "id",
            "identifier",
            "uid",
            "actor_name",
            "rel_obj_app_label",
            "rel_obj_model",
            "rel_obj_id",
            "crontab",
            "paused",
            "next_run",
            "description",
            "last_task_status",
        )

    def get_description(self, instance: Schedule) -> str | None:
        try:
            actor: Actor = get_broker().get_actor(instance.actor_name)
        except ActorNotFound:
            LOGGER.warning("Could not find actor for schedule", schedule=instance)
            return None
        if "description" not in actor.options:
            LOGGER.warning(
                "Could not find description for actor",
                schedule=instance,
                actor=actor.actor_name,
            )
            return None
        return actor.options["description"]

    def get_last_task_status(self, instance: Schedule) -> TaskStatus | None:
        last_task: Task = instance.tasks.defer("message", "result").order_by("-mtime").first()
        if last_task:
            return last_task.aggregated_status
        return None


class ScheduleFilter(FilterSet):
    rel_obj_id__isnull = BooleanFilter("rel_obj_id", "isnull")

    class Meta:
        model = Schedule
        fields = (
            "actor_name",
            "rel_obj_content_type__app_label",
            "rel_obj_content_type__model",
            "rel_obj_id",
            "rel_obj_id__isnull",
            "paused",
        )


class ScheduleViewSet(
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    GenericViewSet,
):
    queryset = (
        Schedule.objects.select_related("rel_obj_content_type")
        .defer("args", "kwargs", "options")
        .all()
    )
    serializer_class = ScheduleSerializer
    search_fields = (
        "id",
        "identifier",
        "_uid",
        "actor_name",
        "rel_obj_content_type__app_label",
        "rel_obj_content_type__model",
        "rel_obj_id",
        "description",
    )
    filterset_class = ScheduleFilter
    ordering = (
        "next_run",
        "actor_name",
        "identifier",
    )

    @permission_required("authentik_tasks_schedules.send_schedule")
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Schedule sent successfully"),
            404: OpenApiResponse(description="Schedule not found"),
            500: OpenApiResponse(description="Failed to send schedule"),
        },
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["POST"])
    def send(self, request: Request, pk=None) -> Response:
        """Trigger this schedule now"""
        schedule: Schedule = self.get_object()
        schedule.send()
        return Response({})
