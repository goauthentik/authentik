"""Tasks API"""
from importlib import import_module

from django.contrib import messages
from django.db.models import Model
from django.http.response import Http404
from django.utils.translation import gettext_lazy as _
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, ChoiceField, DateTimeField, ListField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from authentik.events.monitored_tasks import TaskInfo, TaskResultStatus


class TaskSerializer(Serializer):
    """Serialize TaskInfo and TaskResult"""

    task_name = CharField()
    task_description = CharField()
    task_finish_timestamp = DateTimeField(source="finish_timestamp")

    status = ChoiceField(
        source="result.status.name",
        choices=[(x.name, x.name) for x in TaskResultStatus],
    )
    messages = ListField(source="result.messages")

    def create(self, validated_data: dict) -> Model:
        raise NotImplementedError

    def update(self, instance: Model, validated_data: dict) -> Model:
        raise NotImplementedError


class TaskViewSet(ViewSet):
    """Read-only view set that returns all background tasks"""

    permission_classes = [IsAdminUser]

    @swagger_auto_schema(responses={200: TaskSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """List current messages and pass into Serializer"""
        return Response(TaskSerializer(TaskInfo.all().values(), many=True).data)

    @action(detail=True, methods=["post"])
    # pylint: disable=invalid-name
    def retry(self, request: Request, pk=None) -> Response:
        """Retry task"""
        task = TaskInfo.by_name(pk)
        if not task:
            raise Http404
        try:
            task_module = import_module(task.task_call_module)
            task_func = getattr(task_module, task.task_call_func)
            task_func.delay(*task.task_call_args, **task.task_call_kwargs)
            messages.success(
                self.request,
                _(
                    "Successfully re-scheduled Task %(name)s!"
                    % {"name": task.task_name}
                ),
            )
            return Response(
                {
                    "successful": True,
                }
            )
        except ImportError:  # pragma: no cover
            # if we get an import error, the module path has probably changed
            task.delete()
            return Response({"successful": False})
