"""Tasks API"""
from importlib import import_module

from django.contrib import messages
from django.http.response import Http404
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
from rest_framework.viewsets import ViewSet
from structlog.stdlib import get_logger

from authentik.api.decorators import permission_required
from authentik.core.api.utils import PassiveSerializer
from authentik.events.monitored_tasks import TaskInfo, TaskResultStatus
from authentik.rbac.permissions import HasPermission

LOGGER = get_logger()


class TaskSerializer(PassiveSerializer):
    """Serialize TaskInfo and TaskResult"""

    task_name = CharField()
    task_description = CharField()
    task_finish_timestamp = DateTimeField(source="finish_time")
    task_duration = SerializerMethodField()

    status = ChoiceField(
        source="result.status.name",
        choices=[(x.name, x.name) for x in TaskResultStatus],
    )
    messages = ListField(source="result.messages")

    def get_task_duration(self, instance: TaskInfo) -> int:
        """Get the duration a task took to run"""
        return max(instance.finish_timestamp - instance.start_timestamp, 0)

    def to_representation(self, instance: TaskInfo):
        """When a new version of authentik adds fields to TaskInfo,
        the API will fail with an AttributeError, as the classes
        are pickled in cache. In that case, just delete the info"""
        try:
            return super().to_representation(instance)
        # pylint: disable=broad-except
        except Exception:  # pragma: no cover
            if isinstance(self.instance, list):
                for inst in self.instance:
                    inst.delete()
            else:
                self.instance.delete()
            return {}


class TaskViewSet(ViewSet):
    """Read-only view set that returns all background tasks"""

    permission_classes = [HasPermission("authentik_rbac.view_system_tasks")]
    serializer_class = TaskSerializer

    @extend_schema(
        responses={
            200: TaskSerializer(many=False),
            404: OpenApiResponse(description="Task not found"),
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
    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a single system task"""
        task = TaskInfo.by_name(pk)
        if not task:
            raise Http404
        return Response(TaskSerializer(task, many=False).data)

    @extend_schema(responses={200: TaskSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """List system tasks"""
        tasks = sorted(TaskInfo.all().values(), key=lambda task: task.task_name)
        return Response(TaskSerializer(tasks, many=True).data)

    @permission_required(None, ["authentik_rbac.run_system_tasks"])
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
        task = TaskInfo.by_name(pk)
        if not task:
            raise Http404
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
