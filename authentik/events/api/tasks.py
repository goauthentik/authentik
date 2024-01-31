"""Tasks API"""

from datetime import datetime, timezone
from importlib import import_module

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, ChoiceField, ListField, SerializerMethodField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.events.models import SystemTask, TaskStatus

LOGGER = get_logger()


class SystemTaskSerializer(ModelSerializer):
    """Serialize TaskInfo and TaskResult"""

    name = CharField()
    full_name = SerializerMethodField()
    uid = CharField(required=False)
    description = CharField()
    start_timestamp = SerializerMethodField()
    finish_timestamp = SerializerMethodField()
    duration = SerializerMethodField()

    status = ChoiceField(choices=[(x.value, x.name) for x in TaskStatus])
    messages = ListField(child=CharField())

    def get_full_name(self, instance: SystemTask) -> str:
        """Get full name with UID"""
        if instance.uid:
            return f"{instance.name}:{instance.uid}"
        return instance.name

    def get_start_timestamp(self, instance: SystemTask) -> datetime:
        """Timestamp when the task started"""
        return datetime.fromtimestamp(instance.start_timestamp, tz=timezone.utc)

    def get_finish_timestamp(self, instance: SystemTask) -> datetime:
        """Timestamp when the task finished"""
        return datetime.fromtimestamp(instance.finish_timestamp, tz=timezone.utc)

    def get_duration(self, instance: SystemTask) -> float:
        """Get the duration a task took to run"""
        return max(instance.finish_timestamp - instance.start_timestamp, 0)

    class Meta:
        model = SystemTask
        fields = [
            "uuid",
            "name",
            "full_name",
            "uid",
            "description",
            "start_timestamp",
            "finish_timestamp",
            "duration",
            "status",
            "messages",
        ]


class SystemTaskViewSet(ReadOnlyModelViewSet):
    """Read-only view set that returns all background tasks"""

    queryset = SystemTask.objects.all()
    serializer_class = SystemTaskSerializer
    filterset_fields = ["name", "uid", "status"]
    ordering = ["name", "uid", "status"]
    search_fields = ["name", "description", "uid", "status"]

    @permission_required(None, ["authentik_events.run_task"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Task retried successfully"),
            404: OpenApiResponse(description="Task not found"),
            500: OpenApiResponse(description="Failed to retry task"),
        },
    )
    @action(detail=True, methods=["post"])
    def run(self, request: Request, pk=None) -> Response:
        """Run task"""
        task: SystemTask = self.get_object()
        try:
            task_module = import_module(task.task_call_module)
            task_func = getattr(task_module, task.task_call_func)
            LOGGER.info("Running task", task=task_func)
            task_func.delay(*task.task_call_args, **task.task_call_kwargs)
            messages.success(
                self.request,
                _("Successfully started task %(name)s." % {"name": task.name}),
            )
            return Response(status=204)
        except (ImportError, AttributeError) as exc:  # pragma: no cover
            LOGGER.warning("Failed to run task, remove state", task=task.name, exc=exc)
            # if we get an import error, the module path has probably changed
            task.delete()
            return Response(status=500)
