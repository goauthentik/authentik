"""WebAuthn stage"""

from json import loads
from uuid import UUID

from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError
from webauthn import options_to_json
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url
from webauthn.helpers.exceptions import InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialCreationOptions,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)
from webauthn.registration.generate_registration_options import generate_registration_options
from webauthn.registration.verify_registration_response import (
    VerifiedRegistration,
    verify_registration_response,
)

from authentik.core.api.utils import JSONDictField
from authentik.core.models import User
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallengeMixin,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    AuthenticatorWebAuthnStage,
    WebAuthnDevice,
    WebAuthnDeviceType,
)
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id

SESSION_KEY_WEBAUTHN_CHALLENGE = "authentik/stages/authenticator_webauthn/challenge"


class AuthenticatorWebAuthnChallenge(WithUserInfoChallengeMixin, Challenge):
    """WebAuthn Challenge"""

    registration = JSONDictField()
    component = CharField(default="ak-stage-authenticator-webauthn")


class AuthenticatorWebAuthnChallengeResponse(ChallengeResponse):
    """WebAuthn Challenge response"""

    response = JSONDictField()
    component = CharField(default="ak-stage-authenticator-webauthn")

    request: HttpRequest
    user: User

    def validate_response(self, response: dict) -> dict:
        """Validate webauthn challenge response"""
        challenge = self.request.session[SESSION_KEY_WEBAUTHN_CHALLENGE]

        try:
            registration: VerifiedRegistration = verify_registration_response(
                credential=response,
                expected_challenge=challenge,
                expected_rp_id=get_rp_id(self.request),
                expected_origin=get_origin(self.request),
            )
        except InvalidRegistrationResponse as exc:
            self.stage.logger.warning("registration failed", exc=exc)
            raise ValidationError(f"Registration failed. Error: {exc}") from None

        credential_id_exists = WebAuthnDevice.objects.filter(
            credential_id=bytes_to_base64url(registration.credential_id)
        ).first()
        if credential_id_exists:
            raise ValidationError("Credential ID already exists.")

        stage: AuthenticatorWebAuthnStage = self.stage.executor.current_stage
        aaguid = registration.aaguid
        allowed_aaguids = stage.device_type_restrictions.values_list("aaguid", flat=True)
        if allowed_aaguids.exists():
            invalid_error = ValidationError(
                _(
                    "Invalid device type. Contact your {brand} administrator for help.".format(
                        brand=self.stage.request.brand.branding_title
                    )
                )
            )
            # If there are any restrictions set and we didn't get an aaguid, invalid
            if not aaguid:
                raise invalid_error
            # If one of the restrictions is the "special" unknown device type UUID
            # but we do have a device type for the given aaguid, invalid
            if (
                UUID(UNKNOWN_DEVICE_TYPE_AAGUID) in allowed_aaguids
                and not WebAuthnDeviceType.objects.filter(aaguid=aaguid).exists()
            ):
                return registration
            # Otherwise just check if the given aaguid is in the allowed aaguids
            if UUID(aaguid) not in allowed_aaguids:
                raise invalid_error
        return registration


class AuthenticatorWebAuthnStageView(ChallengeStageView):
    """WebAuthn stage"""

    response_class = AuthenticatorWebAuthnChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        # clear session variables prior to starting a new registration
        self.request.session.pop(SESSION_KEY_WEBAUTHN_CHALLENGE, None)
        stage: AuthenticatorWebAuthnStage = self.executor.current_stage
        user = self.get_pending_user()

        # library accepts none so we store null in the database, but if there is a value
        # set, cast it to string to ensure it's not a django class
        authenticator_attachment = stage.authenticator_attachment
        if authenticator_attachment:
            authenticator_attachment = AuthenticatorAttachment(str(authenticator_attachment))

        registration_options: PublicKeyCredentialCreationOptions = generate_registration_options(
            rp_id=get_rp_id(self.request),
            rp_name=self.request.brand.branding_title,
            user_id=user.uid.encode("utf-8"),
            user_name=user.username,
            user_display_name=user.name,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement(str(stage.resident_key_requirement)),
                user_verification=UserVerificationRequirement(str(stage.user_verification)),
                authenticator_attachment=authenticator_attachment,
            ),
            attestation=AttestationConveyancePreference.DIRECT,
        )

        self.request.session[SESSION_KEY_WEBAUTHN_CHALLENGE] = registration_options.challenge
        self.request.session.save()
        return AuthenticatorWebAuthnChallenge(
            data={
                "registration": loads(options_to_json(registration_options)),
            }
        )

    def get_response_instance(self, data: QueryDict) -> AuthenticatorWebAuthnChallengeResponse:
        response: AuthenticatorWebAuthnChallengeResponse = super().get_response_instance(data)
        response.request = self.request
        response.user = self.get_pending_user()
        return response

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        # Webauthn Challenge has already been validated
        webauthn_credential: VerifiedRegistration = response.validated_data["response"]
        existing_device = WebAuthnDevice.objects.filter(
            credential_id=bytes_to_base64url(webauthn_credential.credential_id)
        ).first()
        if not existing_device:
            name = "WebAuthn Device"
            device_type = WebAuthnDeviceType.objects.filter(
                aaguid=webauthn_credential.aaguid
            ).first()
            if device_type and device_type.description:
                name = device_type.description
            WebAuthnDevice.objects.create(
                name=name,
                user=self.get_pending_user(),
                public_key=bytes_to_base64url(webauthn_credential.credential_public_key),
                credential_id=bytes_to_base64url(webauthn_credential.credential_id),
                sign_count=webauthn_credential.sign_count,
                rp_id=get_rp_id(self.request),
                device_type=device_type,
                aaguid=webauthn_credential.aaguid,
            )
        else:
            return self.executor.stage_invalid("Device with Credential ID already exists.")
        return self.executor.stage_ok()

    def cleanup(self):
        self.request.session.pop(SESSION_KEY_WEBAUTHN_CHALLENGE, None)
