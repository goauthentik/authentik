from django.db import transaction
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.fields import BooleanField, CharField
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from structlog.stdlib import get_logger

from authentik.api.validation import validate
from authentik.core.api.users import UserSelfSerializer
from authentik.core.api.utils import PassiveSerializer
from authentik.endpoints.connectors.agent.auth import AgentAuth
from authentik.endpoints.connectors.agent.models import (
    AgentDeviceConnection,
    AgentDeviceUserBinding,
    AppleUnlockKey,
    DeviceAuthenticationToken,
    DeviceToken,
)
from authentik.enterprise.api import EnterpriseRequiredMixin
from authentik.events.models import Event, EventAction
from authentik.events.utils import model_to_dict

LOGGER = get_logger()


class AgentPSSODeviceStateUser(PassiveSerializer):
    """A user currently registered for Platform SSO on this device"""

    username = CharField()
    enclave_key_id = CharField()


class RegisterDeviceView(APIView):

    class AgentPSSODeviceRegistration(EnterpriseRequiredMixin, PassiveSerializer):
        """Register Apple device via Platform SSO"""

        device_signing_key = CharField()
        device_encryption_key = CharField()
        sign_key_id = CharField()
        enc_key_id = CharField()

    class AgentPSSODeviceRegistrationResponse(PassiveSerializer):
        """authentik settings for Platform SSO tokens"""

        client_id = CharField()
        issuer = CharField()
        token_endpoint = CharField()
        jwks_endpoint = CharField()
        audience = CharField()
        nonce_endpoint = CharField()
        authorization_endpoint = CharField()

    class AgentPSSODeviceState(PassiveSerializer):
        """What authentik currently has stored for this device's Platform SSO
        registration, so the client can detect drift and repair it"""

        device_registered = BooleanField()
        sign_key_id = CharField(allow_blank=True)
        enc_key_id = CharField(allow_blank=True)
        users = AgentPSSODeviceStateUser(many=True)

    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = []
    serializer_class = AgentPSSODeviceRegistration
    authentication_classes = [AgentAuth]

    @extend_schema(
        responses={
            200: AgentPSSODeviceState(),
        }
    )
    def get(self, request: Request) -> Response:
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        users = AgentDeviceUserBinding.objects.filter(
            target=conn.device, connector=conn.connector
        ).select_related("user")
        return Response(
            data={
                "device_registered": bool(conn.apple_signing_key),
                "sign_key_id": conn.apple_sign_key_id,
                "enc_key_id": conn.apple_enc_key_id,
                "users": [
                    {
                        "username": binding.user.username,
                        "enclave_key_id": binding.apple_enclave_key_id,
                    }
                    for binding in users
                ],
            }
        )

    @extend_schema(responses={204: None})
    @transaction.atomic()
    def delete(self, request: Request) -> Response:
        """Clear this device's Platform SSO registration, used when the configuration
        profile is removed from the device. The device stays enrolled otherwise."""
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        conn.apple_signing_key = ""
        conn.apple_encryption_key = ""
        conn.apple_key_exchange_key = ""
        conn.apple_sign_key_id = ""
        conn.apple_enc_key_id = ""
        conn.save()
        bindings = AgentDeviceUserBinding.objects.filter(
            target=conn.device, connector=conn.connector
        )
        # Unlock keys hang off the bindings and are useless without the enclave key
        AppleUnlockKey.objects.filter(device_user__in=bindings).delete()
        bindings.update(apple_secure_enclave_key="", apple_enclave_key_id="")
        DeviceAuthenticationToken.objects.filter(device=conn.device).delete()
        LOGGER.info("Cleared Platform SSO registration", device=conn.device.name)
        Event.new(
            EventAction.MODEL_UPDATED,
            model=model_to_dict(conn),
            message="Platform SSO registration removed",
        ).from_http(request)
        return Response(status=204)

    @extend_schema(
        responses={
            200: AgentPSSODeviceRegistrationResponse(),
        }
    )
    @validate(AgentPSSODeviceRegistration)
    def post(self, request: Request, body: AgentPSSODeviceRegistration) -> Response:
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        conn.apple_signing_key = body.validated_data["device_signing_key"]
        conn.apple_encryption_key = body.validated_data["device_encryption_key"]
        conn.apple_key_exchange_key = body.validated_data["device_encryption_key"]
        conn.apple_sign_key_id = body.validated_data["sign_key_id"]
        conn.apple_enc_key_id = body.validated_data["enc_key_id"]
        conn.save()
        return Response(
            data={
                "client_id": str(conn.connector.pk),
                "issuer": self.request.build_absolute_uri(
                    reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
                ),
                "audience": str(conn.device.pk),
                "token_endpoint": request.build_absolute_uri(
                    reverse("authentik_enterprise_endpoints_connectors_agent:psso-token")
                ),
                "jwks_endpoint": request.build_absolute_uri(
                    reverse("authentik_enterprise_endpoints_connectors_agent:psso-jwks")
                ),
                "nonce_endpoint": request.build_absolute_uri(
                    reverse("authentik_enterprise_endpoints_connectors_agent:psso-nonce")
                ),
                "authorization_endpoint": request.build_absolute_uri(
                    reverse(
                        "authentik_enterprise_endpoints_connectors_agent:psso-preauthenticate",
                        kwargs={"connector_uuid": str(conn.connector.pk)},
                    )
                ),
            }
        )


class RegisterUserView(APIView):

    class AgentPSSOUserRegistration(EnterpriseRequiredMixin, PassiveSerializer):
        """Register Apple device user via Platform SSO"""

        user_auth = CharField()
        user_secure_enclave_key = CharField()
        enclave_key_id = CharField()

    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = []
    serializer_class = AgentPSSOUserRegistration
    authentication_classes = [AgentAuth]

    @extend_schema(
        responses={
            200: UserSelfSerializer(),
        }
    )
    @validate(AgentPSSOUserRegistration)
    def post(self, request: Request, body: AgentPSSOUserRegistration) -> Response:
        device_token: DeviceToken = request.auth
        conn: AgentDeviceConnection = device_token.device
        user_token = DeviceAuthenticationToken.objects.filter(
            device=conn.device,
            token=body.validated_data["user_auth"],
            device_token=device_token,
        ).first()
        if not user_token:
            raise ValidationError("Invalid user authentication")
        # These fields must be set on create as well as update; update_or_create() returns
        # immediately when it creates, so anything only in `defaults` is never applied.
        enclave_keys = {
            "apple_secure_enclave_key": body.validated_data["user_secure_enclave_key"],
            "apple_enclave_key_id": body.validated_data["enclave_key_id"],
        }
        AgentDeviceUserBinding.objects.update_or_create(
            target=conn.device,
            user=user_token.user,
            connector=conn.connector,
            create_defaults={
                "is_primary": True,
                "order": 0,
                **enclave_keys,
            },
            defaults=enclave_keys,
        )
        return Response(
            UserSelfSerializer(instance=user_token.user, context={"request": request}).data
        )
