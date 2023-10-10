"""Meta API"""
from drf_spectacular.utils import extend_schema
from rest_framework.fields import CharField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.core.api.utils import PassiveSerializer
from authentik.lib.utils.reflection import get_apps
from authentik.policies.event_matcher.models import model_choices


class AppSerializer(PassiveSerializer):
    """Serialize Application info"""

    name = CharField()
    label = CharField()


class AppsViewSet(ViewSet):
    """Read-only view list all installed apps"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AppSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Read-only view list all installed apps"""
        data = []
        for app in sorted(get_apps(), key=lambda app: app.name):
            data.append({"name": app.name, "label": app.verbose_name})
        return Response(AppSerializer(data, many=True).data)


class ModelViewSet(ViewSet):
    """Read-only view list all installed models"""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AppSerializer(many=True)})
    def list(self, request: Request) -> Response:
        """Read-only view list all installed models"""
        data = []
        for name, label in model_choices():
            data.append({"name": name, "label": label})
        return Response(AppSerializer(data, many=True).data)
