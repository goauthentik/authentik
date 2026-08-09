"""Meta API"""

from django.apps import apps
from drf_spectacular.utils import extend_schema
from rest_framework.fields import BooleanField, CharField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.api.validation import validate
from authentik.core.api.utils import PassiveSerializer
from authentik.core.models import AttributesMixin
from authentik.lib.api import Models
from authentik.lib.utils.reflection import get_apps


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

    class ModelFilterSerializer(PassiveSerializer):
        filter_has_attributes = BooleanField(allow_null=True, default=None)

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AppSerializer(many=True)}, parameters=[ModelFilterSerializer])
    @validate(ModelFilterSerializer, "query")
    def list(self, request: Request, query: ModelFilterSerializer) -> Response:
        """Read-only view list all installed models"""
        data = []
        for name, label in Models.choices:
            if query.validated_data["filter_has_attributes"]:
                if not issubclass(apps.get_model(name), AttributesMixin):
                    continue
            data.append({"name": name, "label": label})
        return Response(AppSerializer(data, many=True).data)
