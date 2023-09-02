"""AuthenticatorMobileStage API Views"""
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import mixins
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.decorators import action
from rest_framework.fields import CharField, UUIDField

from rest_framework.request import Request
from rest_framework.response import Response
from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.stages.authenticator_mobile.api.auth import MobileDeviceTokenAuthentication
from authentik.stages.authenticator_mobile.models import MobileDevice


class MobileDeviceSerializer(ModelSerializer):
    """Serializer for Mobile authenticator devices"""

    class Meta:
        model = MobileDevice
        fields = ["pk", "name"]
        depth = 2


class MobileDeviceViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    UsedByMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    """Viewset for Mobile authenticator devices"""

    queryset = MobileDevice.objects.all()
    serializer_class = MobileDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
    permission_classes = [OwnerPermissions]
    filter_backends = [OwnerFilter, DjangoFilterBackend, OrderingFilter, SearchFilter]

    @extend_schema(
        responses={
            204: "",
        },
        request=inline_serializer(
            "MobileDeviceSetPushKeySerializer",
            {
                "firebase_key": CharField(required=True),
            },
        ),
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def set_notification_key(self):
        """Called by the phone whenever the firebase key changes and we need to update it"""
        device = self.get_object()
        print(self.request.user)

    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def receive_response():
        """Get response from notification on phone"""
        pass

    @extend_schema(
        responses={
            200: inline_serializer(
                "MobileDeviceEnrollmentCallbackSerializer",
                {
                    "device_token": CharField(required=True),
                    "device_uuid": UUIDField(required=True)
                },
            ),
        },
        request=inline_serializer(
            "MobileDeviceEnrollmentSerializer",
            {
                # New API token (that will be rotated at some point)
                # also used by the backend to sign requests to the cloud broker
                # also used by the app to check the signature of incoming requests
                "token": CharField(required=True),
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


class AdminMobileDeviceViewSet(ModelViewSet):
    """Viewset for Mobile authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = MobileDevice.objects.all()
    serializer_class = MobileDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
