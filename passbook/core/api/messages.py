"""core messages API"""
from django.contrib.messages import get_messages
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ReadOnlyField, Serializer
from rest_framework.viewsets import ViewSet


class MessageSerializer(Serializer):
    """Serialize Django Message into DRF Object"""

    message = ReadOnlyField()
    level = ReadOnlyField()
    tags = ReadOnlyField()
    extra_tags = ReadOnlyField()
    level_tag = ReadOnlyField()

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class MessagesViewSet(ViewSet):
    """Read-only view set that returns the current session's messages"""

    permission_classes = [AllowAny]

    @swagger_auto_schema(responses={200: MessageSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """List current messages and pass into Serializer"""
        all_messages = list(get_messages(request))
        return Response(MessageSerializer(all_messages, many=True).data)
