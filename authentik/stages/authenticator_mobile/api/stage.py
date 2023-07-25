"""AuthenticatorMobileStage API Views"""
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.fields import CharField
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from authentik.core.api.used_by import UsedByMixin
from authentik.flows.api.stages import StageSerializer
from authentik.stages.authenticator_mobile.api.auth import MobileDeviceTokenAuthentication
from authentik.stages.authenticator_mobile.models import AuthenticatorMobileStage


class AuthenticatorMobileStageSerializer(StageSerializer):
    """AuthenticatorMobileStage Serializer"""

    class Meta:
        model = AuthenticatorMobileStage
        fields = StageSerializer.Meta.fields + [
            "configure_flow",
            "friendly_name",
        ]


class AuthenticatorMobileStageViewSet(UsedByMixin, ModelViewSet):
    """AuthenticatorMobileStage Viewset"""

    queryset = AuthenticatorMobileStage.objects.all()
    serializer_class = AuthenticatorMobileStageSerializer
    filterset_fields = [
        "name",
        "configure_flow",
    ]
    search_fields = ["name"]
    ordering = ["name"]

    @extend_schema(
        responses={
            200: inline_serializer(
                "MobileDeviceEnrollmentCallbackSerializer",
                {
                    "device_token": CharField(required=True),
                },
            ),
        },
        request=inline_serializer(
            "MobileDeviceEnrollmentSerializer",
            {
                "device_token": CharField(required=True),
            },
        ),
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def enrollment_callback(self, request: Request, pk: str) -> Response:
        """Enrollment callback"""
        print(request.data)
        return Response(status=204)
