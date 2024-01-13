"""Tasks API"""
from importlib import import_module

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.fields import (
    CharField,
    ChoiceField,
    DateTimeField,
    ListField,
    SerializerMethodField,
)
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

    task_name = CharField(source="name")
    task_description = CharField(source="description")
    task_start_timestamp = DateTimeField(source="start_timestamp")
    task_finish_timestamp = DateTimeField(source="finish_timestamp")
    task_duration = SerializerMethodField()

    status = ChoiceField(
        # source="status",
        choices=[(x.name, x.name) for x in TaskStatus],
    )
    messages = ListField(child=CharField())

    def get_task_duration(self, instance: SystemTask) -> int:
        """Get the duration a task took to run"""
        return max(instance.finish_timestamp.timestamp() - instance.start_timestamp.timestamp(), 0)

    class Meta:
        model = SystemTask
        fields = [
            "task_name",
            "task_description",
            "task_start_timestamp",
            "task_finish_timestamp",
            "task_duration",
            "status",
            "messages",
        ]


class SystemTaskViewSet(ReadOnlyModelViewSet):
    """Read-only view set that returns all background tasks"""

    queryset = SystemTask.objects.all()
    serializer_class = SystemTaskSerializer

    @permission_required(None, ["authentik_events.rerun_task"])
    @extend_schema(
        request=OpenApiTypes.NONE,
        responses={
            204: OpenApiResponse(description="Task retried successfully"),
            404: OpenApiResponse(description="Task not found"),
            500: OpenApiResponse(description="Failed to retry task"),
        },
        parameters=[
            OpenApiParameter(
                "id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
            ),
        ],
    )
    @action(detail=True, methods=["post"])
    def retry(self, request: Request, pk=None) -> Response:
        """Retry task"""
        task = self.get_object()
        try:
            task_module = import_module(task.task_call_module)
            task_func = getattr(task_module, task.task_call_func)
            LOGGER.debug("Running task", task=task_func)
            task_func.delay(*task.task_call_args, **task.task_call_kwargs)
            messages.success(
                self.request,
                _("Successfully re-scheduled Task %(name)s!" % {"name": task.task_name}),
            )
            return Response(status=204)
        except (ImportError, AttributeError):  # pragma: no cover
            LOGGER.warning("Failed to run task, remove state", task=task)
            # if we get an import error, the module path has probably changed
            task.delete()
            return Response(status=500)
