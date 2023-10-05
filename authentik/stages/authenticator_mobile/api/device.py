"""AuthenticatorMobileStage API Views"""
from django.http import Http404
from django.utils.timezone import now
from django_filters.rest_framework.backends import DjangoFilterBackend
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.fields import CharField, ChoiceField, JSONField, UUIDField
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from authentik.api.authorization import OwnerFilter, OwnerPermissions
from authentik.core.api.used_by import UsedByMixin
from authentik.core.api.utils import PassiveSerializer
from authentik.stages.authenticator_mobile.api.auth import MobileDeviceTokenAuthentication
from authentik.stages.authenticator_mobile.models import (
    MobileDevice,
    MobileDeviceToken,
    MobileTransaction,
    TransactionStates,
)


class MobileDeviceInfoSerializer(PassiveSerializer):
    """Info about a mobile device"""

    platform = ChoiceField(
        (
            ("ios", "iOS"),
            ("android", "Android"),
        )
    )
    os_version = CharField()
    model = CharField()
    hostname = CharField()
    app_version = CharField()

    others = JSONField()


class MobileDeviceSerializer(ModelSerializer):
    """Serializer for Mobile authenticator devices"""

    last_checkin = MobileDeviceInfoSerializer(read_only=True)

    class Meta:
        model = MobileDevice
        fields = ["pk", "name", "state", "last_checkin"]
        depth = 2


class MobileDeviceCheckInSerializer(PassiveSerializer):
    """Check info into authentik"""

    info = MobileDeviceInfoSerializer()


class MobileDeviceEnrollmentSerializer(PassiveSerializer):
    """Enrollment request, send the device's unique identifier"""

    device_uid = CharField(required=True)
    info = MobileDeviceInfoSerializer()


class MobileDeviceSetPushKeySerializer(PassiveSerializer):
    """Set notification key"""

    firebase_key = CharField(required=True)


class MobileDeviceResponseSerializer(PassiveSerializer):
    """Response from push sent to phone"""

    tx_id = UUIDField(required=True)
    status = ChoiceField(
        TransactionStates.choices,
        required=True,
    )


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
            200: inline_serializer(
                "MobileDeviceEnrollmentCallbackSerializer",
                {
                    # New API token (that will be rotated at some point)
                    # also used by the backend to sign requests to the cloud broker
                    # also used by the app to check the signature of incoming requests
                    "token": CharField(required=True),
                },
            ),
        },
        request=MobileDeviceEnrollmentSerializer,
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        filter_backends=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def enrollment_callback(self, request: Request, pk: str) -> Response:
        """Enrollment callback"""
        device: MobileDevice = self.get_object()
        data = MobileDeviceEnrollmentSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        device.name = data.validated_data["info"]["hostname"]
        device.confirmed = True
        device.device_id = data.validated_data["device_uid"]
        device.save()
        MobileDeviceToken.objects.filter(
            device=device,
        ).delete()
        new_token = MobileDeviceToken.objects.create(
            device=device,
            user=device.user,
        )
        return Response(
            data={
                "token": new_token.token,
            }
        )

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                "MobileDeviceEnrollmentStatusSerializer",
                {
                    "status": ChoiceField(
                        (
                            ("success", "Success"),
                            ("waiting", "Waiting"),
                        )
                    )
                },
            ),
        },
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        filter_backends=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def enrollment_status(self, request: Request, pk: str) -> Response:
        """Check device enrollment status"""
        device: MobileDevice = self.get_object()
        return Response({"status": "success" if device.confirmed else "waiting"})

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Key successfully set"),
        },
        request=MobileDeviceSetPushKeySerializer,
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        filter_backends=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def set_notification_key(self, request: Request, pk: str) -> Response:
        """Called by the phone whenever the firebase key changes and we need to update it"""
        device: MobileDevice = self.get_object()
        data = MobileDeviceSetPushKeySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        device.firebase_token = data.validated_data["firebase_key"]
        device.save()
        return Response(status=204)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Key successfully set"),
            404: OpenApiResponse(description="Transaction not found"),
        },
        request=MobileDeviceResponseSerializer,
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        filter_backends=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def receive_response(self, request: Request, pk: str) -> Response:
        """Get response from notification on phone"""
        data = MobileDeviceResponseSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        transaction = MobileTransaction.objects.filter(tx_id=data.validated_data["tx_id"]).first()
        if not transaction:
            raise Http404
        transaction.status = data.validated_data["status"]
        transaction.save()
        return Response(status=204)

    @extend_schema(
        responses={
            204: OpenApiResponse(description="Checked in"),
        },
        request=MobileDeviceInfoSerializer,
    )
    @action(
        methods=["POST"],
        detail=True,
        permission_classes=[],
        filter_backends=[],
        authentication_classes=[MobileDeviceTokenAuthentication],
    )
    def check_in(self, request: Request, pk: str) -> Response:
        """Check in data about a device"""
        data = MobileDeviceInfoSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        device: MobileDevice = self.get_object()
        device.last_checkin = now()
        device.state = data.validated_data
        device.save()
        return Response(status=204)


class AdminMobileDeviceViewSet(ModelViewSet):
    """Viewset for Mobile authenticator devices (for admins)"""

    permission_classes = [IsAdminUser]
    queryset = MobileDevice.objects.all()
    serializer_class = MobileDeviceSerializer
    search_fields = ["name"]
    filterset_fields = ["name"]
    ordering = ["name"]
