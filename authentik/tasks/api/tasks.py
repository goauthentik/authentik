from django_dramatiq_postgres.models import TaskState
from django_filters.filters import BooleanFilter, MultipleChoiceFilter
from django_filters.filterset import FilterSet
from dramatiq.actor import Actor
from dramatiq.broker import get_broker
from dramatiq.errors import ActorNotFound
from dramatiq.message import Message
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import ReadOnlyField, SerializerMethodField
from rest_framework.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import ModelSerializer
from authentik.events.logs import LogEventSerializer
from authentik.rbac.decorators import permission_required
from authentik.tasks.models import Task, TaskStatus
from authentik.tenants.utils import get_current_tenant

LOGGER = get_logger()


class TaskSerializer(ModelSerializer):
    rel_obj_app_label = ReadOnlyField(source="rel_obj_content_type.app_label")
    rel_obj_model = ReadOnlyField(source="rel_obj_content_type.model")

    messages = LogEventSerializer(many=True, source="_messages")
    previous_messages = LogEventSerializer(many=True, source="_previous_messages")
    description = SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "message_id",
            "queue_name",
            "actor_name",
            "state",
            "mtime",
            "rel_obj_app_label",
            "rel_obj_model",
            "rel_obj_id",
            "uid",
            "messages",
            "previous_messages",
            "aggregated_status",
            "description",
        ]

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


class TaskFilter(FilterSet):
    rel_obj_id__isnull = BooleanFilter("rel_obj_id", "isnull")
    aggregated_status = MultipleChoiceFilter(
        choices=TaskStatus.choices,
        field_name="aggregated_status",
    )

    class Meta:
        model = Task
        fields = (
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
            .defer("message", "result")
            .filter(tenant=get_current_tenant())
        )

    @permission_required(None, ["authentik_tasks.retry_task"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Task retried successfully"),
            400: OpenApiResponse(description="Task is not in a retryable state"),
            404: OpenApiResponse(description="Task not found"),
        },
    )
    @action(detail=True, methods=["POST"], permission_classes=[])
    def retry(self, request: Request, pk=None) -> Response:
        """Retry task"""
        task: Task = self.get_object()
        if task.state not in (TaskState.REJECTED, TaskState.DONE):
            return Response(status=400)
        broker = get_broker()
        broker.enqueue(Message.decode(task.message))
        return Response(status=204)
