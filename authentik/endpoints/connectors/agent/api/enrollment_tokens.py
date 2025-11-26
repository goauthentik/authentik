from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.tokens import TokenViewSerializer
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import ModelSerializer
from authentik.endpoints.api.device_tags import DeviceTagSerializer
from authentik.endpoints.connectors.agent.models import EnrollmentToken
from authentik.events.models import Event, EventAction
from authentik.rbac.decorators import permission_required


class EnrollmentTokenSerializer(ModelSerializer):

    device_tags_obj = DeviceTagSerializer(
        source="device_tags", many=True, read_only=True, required=False
    )

    class Meta:
        model = EnrollmentToken
        fields = [
            "token_uuid",
            "device_tags",
            "device_tags_obj",
            "connector",
            "name",
            "expiring",
            "expires",
        ]


class EnrollmentTokenViewSet(UsedByMixin, ModelViewSet):

    queryset = EnrollmentToken.objects.all().prefetch_related("device_tags")
    serializer_class = EnrollmentTokenSerializer
    search_fields = [
        "name",
        "connector__name",
    ]
    ordering = ["token_uuid"]
    filterset_fields = ["token_uuid", "connector"]

    @permission_required("authentik_endpoints_connectors_agent.view_enrollment_token_key")
    @extend_schema(
        responses={
            200: TokenViewSerializer(many=False),
            404: OpenApiResponse(description="Token not found or expired"),
        }
    )
    @action(detail=True, pagination_class=None, filter_backends=[], methods=["GET"])
    def view_key(self, request: Request, pk: str) -> Response:
        """Return token key and log access"""
        token: EnrollmentToken = self.get_object()
        Event.new(EventAction.SECRET_VIEW, secret=token).from_http(request)  # noqa # nosec
        return Response(TokenViewSerializer({"key": token.key}).data)
