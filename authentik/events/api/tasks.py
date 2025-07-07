"""Tasks API"""

from importlib import import_module

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    ChoiceField,
    DateTimeField,
    FloatField,
    SerializerMethodField,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from structlog.stdlib import get_logger

from authentik.core.api.utils import ModelSerializer
from authentik.events.logs import LogEventSerializer
from authentik.events.models import SystemTask, TaskStatus
from authentik.rbac.decorators import permission_required

LOGGER = get_logger()


class SystemTaskSerializer(ModelSerializer):
    """Serialize TaskInfo and TaskResult"""

    name = CharField()
    full_name = SerializerMethodField()
    uid = CharField(required=False)
    description = CharField()
    start_timestamp = DateTimeField(read_only=True)
    finish_timestamp = DateTimeField(read_only=True)
    duration = FloatField(read_only=True)

    status = ChoiceField(choices=[(x.value, x.name) for x in TaskStatus])
    messages = LogEventSerializer(many=True)

    def get_full_name(self, instance: SystemTask) -> str:
        """Get full name with UID"""
        if instance.uid:
            return f"{instance.name}:{instance.uid}"
        return instance.name

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
            "expires",
            "expiring",
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
    @action(detail=True, methods=["POST"], permission_classes=[])
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
                _("Successfully started task {name}.".format_map({"name": task.name})),
            )
            return Response(status=204)
        except (ImportError, AttributeError) as exc:  # pragma: no cover
            LOGGER.warning("Failed to run task, remove state", task=task.name, exc=exc)
            # if we get an import error, the module path has probably changed
            task.delete()
            return Response(status=500)
