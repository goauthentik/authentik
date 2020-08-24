"""passbook config viewsets"""
from drf_yasg.utils import swagger_auto_schema
from rest_framework.fields import BooleanField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ReadOnlyField, Serializer
from rest_framework.viewsets import ViewSet

from passbook.lib.config import CONFIG


class ConfigSerializer(Serializer):
    """Serialize somehat public fields for authenticated users"""

    log_level = ReadOnlyField()
    error_reporting_enabled = BooleanField(
        read_only=True, source="error_reporting.enabled"
    )
    error_reporting_environment = ReadOnlyField(source="error_reporting.environment")

    def create(self, request: Request) -> Response:
        raise NotImplementedError

    def update(self, request: Request) -> Response:
        raise NotImplementedError


class ConfigViewSet(ViewSet):
    """Retrieve passbook configurations"""

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: ConfigSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Retrieve passbook configurations"""
        return Response([ConfigSerializer(CONFIG.raw).data])
