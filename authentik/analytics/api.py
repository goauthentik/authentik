"""authentik analytics api"""

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.fields import CharField, DictField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from authentik.analytics.utils import get_analytics_data, get_analytics_description
from authentik.core.api.utils import PassiveSerializer
from authentik.rbac.permissions import HasPermission


class AnalyticsDescriptionSerializer(PassiveSerializer):
    label = CharField()
    desc = CharField()


class AnalyticsDescriptionViewSet(ViewSet):
    """Read-only view of analytics descriptions"""

    permission_classes = [HasPermission("authentik_rbac.view_system_settings")]

    @extend_schema(responses={200: AnalyticsDescriptionSerializer})
    def list(self, request: Request) -> Response:
        """Read-only view of analytics descriptions"""
        data = []
        for label, desc in get_analytics_description().items():
            data.append({"label": label, "desc": desc})
        return Response(AnalyticsDescriptionSerializer(data, many=True).data)


class AnalyticsDataViewSet(ViewSet):
    """Read-only view of analytics descriptions"""

    permission_classes = [HasPermission("authentik_rbac.edit_system_settings")]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="AnalyticsData",
                fields={
                    "data": DictField(),
                },
            )
        }
    )
    def list(self, request: Request) -> Response:
        """Read-only view of analytics descriptions"""
        return Response(
            {
                "data": get_analytics_data(force=True),
            }
        )
