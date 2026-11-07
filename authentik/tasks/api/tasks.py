from typing import cast

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count
from django_dramatiq_postgres.models import TaskState
from django_filters.filters import BaseInFilter, BooleanFilter, MultipleChoiceFilter, UUIDFilter
from django_filters.filterset import FilterSet
from dramatiq.actor import Actor
from dramatiq.broker import get_broker
from dramatiq.errors import ActorNotFound
from dramatiq.message import Message
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
    inline_serializer,
)
from rest_framework.decorators import action
from rest_framework.fields import IntegerField, ReadOnlyField, SerializerMethodField
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import ModelSerializer
from authentik.events.logs import LogEventSerializer
from authentik.rbac.decorators import permission_required
from authentik.tasks.models import Task, TaskLog, TaskStatus

LOGGER = get_logger()


class TaskSerializer(ModelSerializer):
    rel_obj_app_label = ReadOnlyField(source="rel_obj_content_type.app_label")
    rel_obj_model = ReadOnlyField(source="rel_obj_content_type.model")

    logs = SerializerMethodField()
    previous_logs = SerializerMethodField()

    description = SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "message_id",
            "queue_name",
            "actor_name",
            "state",
            "mtime",
            "retries",
            "eta",
            "rel_obj_app_label",
            "rel_obj_model",
            "rel_obj_id",
            "uid",
            "logs",
            "previous_logs",
            "aggregated_status",
            "description",
        ]

    def _tasklogs(self, instance: Task, previous: bool) -> list[TaskLog]:
        # The viewset prefetches tasklogs; filtering them with .filter() would run a
        # new query for every task in the page, so filter the prefetched list instead.
        return [log for log in instance.tasklogs.all() if log.previous == previous]

    @extend_schema_field(LogEventSerializer(many=True))
    def get_logs(self, instance: Task):
        return cast(ReturnList, LogEventSerializer(instance._messages, many=True).data) + cast(
            ReturnList, LogEventSerializer(self._tasklogs(instance, False), many=True).data
        )

    @extend_schema_field(LogEventSerializer(many=True))
    def get_previous_logs(self, instance: Task):
        return cast(ReturnList, LogEventSerializer(instance._messages, many=True).data) + cast(
            ReturnList, LogEventSerializer(self._tasklogs(instance, True), many=True).data
        )

    def get_description(self, instance: Task) -> str | None:
        try:
            actor: Actor = get_broker().get_actor(instance.actor_name)
        except ActorNotFound:
            LOGGER.warning("Could not find actor for schedule", schedule=instance)
            return None
        if "description" not in actor.options:
            LOGGER.warning(
                "Could not find description for actor",
                task=instance,
                actor=actor.actor_name,
            )
            return None
        return actor.options["description"]


class UUIDInFilter(BaseInFilter, UUIDFilter):
    pass


class TaskFilter(FilterSet):
    rel_obj_id__isnull = BooleanFilter("rel_obj_id", "isnull")
    aggregated_status = MultipleChoiceFilter(
        choices=TaskStatus.choices,
        field_name="aggregated_status",
        # A filter on a column of the task itself cannot return a task twice. The default
        # DISTINCT makes the page count compare every selected column of every task.
        distinct=False,
    )
    message_id__in = UUIDInFilter(field_name="message_id", lookup_expr="in")

    def filter_queryset(self, queryset):
        # Postgres cannot tell how many tasks a joined content type matches, and sorts every task
        # of the object to find the newest. Given the content type's ID, it reads the newest
        # tasks from the index on (content type, object, mtime).
        content_type = {}
        for lookup in ("app_label", "model"):
            if value := self.form.cleaned_data.pop(f"rel_obj_content_type__{lookup}", None):
                content_type[lookup] = value
        if content_type:
            queryset = queryset.filter(
                rel_obj_content_type__in=list(
                    ContentType.objects.filter(**content_type).values_list("pk", flat=True)
                )
            )
        return super().filter_queryset(queryset)

    class Meta:
        model = Task
        fields = (
            "message_id",
            "message_id__in",
            "queue_name",
            "actor_name",
            "state",
            "rel_obj_content_type__app_label",
            "rel_obj_content_type__model",
            "rel_obj_id",
            "rel_obj_id__isnull",
            "aggregated_status",
        )


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
        "rel_obj_content_type__app_label",
        "rel_obj_content_type__model",
        "rel_obj_id",
        "_uid",
        "aggregated_status",
    )
    filterset_class = TaskFilter
    ordering = ("-mtime",)

    def get_queryset(self):
        return (
            Task.objects.select_related("rel_obj_content_type")
            .prefetch_related("tasklogs")
            .defer("message", "result")
        )

    @permission_required("authentik_tasks.retry_task")
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Task retried successfully"),
            400: OpenApiResponse(description="Task is not in a retryable state"),
            404: OpenApiResponse(description="Task not found"),
        },
    )
    @action(detail=True, methods=["POST"], permission_classes=[IsAuthenticated])
    def retry(self, request: Request, pk=None) -> Response:
        """Retry task"""
        task: Task = self.get_object()
        if task.state != TaskState.REJECTED:
            return Response(status=400)
        broker = get_broker()
        broker.enqueue(Message.decode(task.message))
        return Response(status=204)

    @permission_required(None, ["authentik_tasks.view_task"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            200: inline_serializer(
                "GlobalTaskStatusSerializer",
                {
                    "queued": IntegerField(read_only=True),
                    "consumed": IntegerField(read_only=True),
                    "preprocess": IntegerField(read_only=True),
                    "running": IntegerField(read_only=True),
                    "postprocess": IntegerField(read_only=True),
                    "rejected": IntegerField(read_only=True),
                    "done": IntegerField(read_only=True),
                    "info": IntegerField(read_only=True),
                    "warning": IntegerField(read_only=True),
                    "error": IntegerField(read_only=True),
                },
            ),
        },
    )
    @action(detail=False, methods=["GET"], permission_classes=[IsAuthenticated])
    def status(self, request: Request) -> Response:
        """Global status summary for all tasks"""
        response = {}
        for status in (
            Task.objects.all()
            .values("aggregated_status")
            .annotate(count=Count("aggregated_status"))
        ):
            response[status["aggregated_status"]] = status["count"]
        return Response(
            {
                "queued": response.get("queued", 0),
                "consumed": response.get("consumed", 0),
                "preprocess": response.get("preprocess", 0),
                "running": response.get("running", 0),
                "postprocess": response.get("postprocess", 0),
                "rejected": response.get("rejected", 0),
                "done": response.get("done", 0),
                "info": response.get("info", 0),
                "warning": response.get("warning", 0),
                "error": response.get("error", 0),
            }
        )
