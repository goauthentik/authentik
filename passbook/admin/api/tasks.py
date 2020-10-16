"""Tasks API"""
from importlib import import_module

from django.contrib import messages
from django.http.response import Http404
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.fields import CharField, DateTimeField, IntegerField, ListField
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from passbook.lib.tasks import TaskInfo


class TaskSerializer(Serializer):
    """Serialize TaskInfo and TaskResult"""

    task_name = CharField()
    task_description = CharField()
    task_finish_timestamp = DateTimeField(source="finish_timestamp")

    status = IntegerField(source="result.status.value")
    messages = ListField(source="result.messages")

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
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
        task_module = import_module(task.task_call_module)
        task_func = getattr(task_module, task.task_call_func)
        task_func.delay(*task.task_call_args, **task.task_call_kwargs)
        messages.success(self.request, _("Successfully re-scheduled Task %(name)s!" % {'name': task.task_name}))
        return Response(
            {
                "successful": True,
            }
        )
