from base64 import urlsafe_b64decode

from django.db.models import QuerySet
from django.utils.translation import gettext as _
from structlog.stdlib import get_logger
from webauthn import (
    base64url_to_bytes,
    generate_authentication_options,
    verify_authentication_response,
)
from webauthn.helpers import options_to_json_dict, parse_authentication_credential_json
from webauthn.helpers.exceptions import InvalidAuthenticationResponse, InvalidJSONStructure
from webauthn.helpers.structs import (
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    UserVerificationRequirement,
)

from authentik.core.models import User
from authentik.events.middleware import audit_ignore
from authentik.stages.authenticator_validate.challenge.base import (
    ChallengeValidationError,
    DeviceChallenge,
    DeviceChallenger,
)
from authentik.stages.authenticator_webauthn.models import UserVerification, WebAuthnDevice
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id

LOGGER = get_logger()


class WebAuthnChallenger(DeviceChallenger):

    device_class = WebAuthnDevice

    def _make_webauthn_challenge(self, allowed_credentials: list[PublicKeyCredentialDescriptor]):
        authentication_options = generate_authentication_options(
            rp_id=get_rp_id(self.request),
            allow_credentials=allowed_credentials,
            user_verification=UserVerificationRequirement(
                self.validate_stage.webauthn_user_verification
            ),
        )

        options_dict = options_to_json_dict(authentication_options)

        if self.validate_stage.webauthn_hints:
            options_dict["hints"] = list(self.validate_stage.webauthn_hints)
        return options_dict

    def make_device_challenges(self, user: User) -> list[DeviceChallenge]:
        devices = WebAuthnDevice.objects.filter(user=user)
        if self.validate_stage.webauthn_allowed_device_types.exists():
            devices = devices.filter(
                device_type__in=self.validate_stage.webauthn_allowed_device_types.all()
            )

        allowed_credentials = []

        # We want all the user's WebAuthn devices and merge their challenges
        for user_device in devices.order_by("name"):
            allowed_credentials.append(user_device.descriptor)

        if len(allowed_credentials) == 0:
            return []

        return [
            self._make_device_challenge(
                None, user, self._make_webauthn_challenge(allowed_credentials)
            )
        ]

    def make_identification_challenge(self) -> DeviceChallenge:
        return self._make_device_challenge(None, None, self.make_raw_identification_challenge())

    def make_raw_identification_challenge(self) -> dict:
        """
        Creates a challenge that can be used to authenticate any user.
        """
        return self._make_webauthn_challenge([])

    def initiate(self, device_challenge: dict):
        pass

    def validate(
        self, devices: QuerySet[WebAuthnDevice], challenge: dict, challenge_response: str | dict
    ) -> WebAuthnDevice:

        if "MinuteMaid" in self.request.META.get("HTTP_USER_AGENT", ""):
            # Workaround for Android sign-in, when signing into Google Workspace on android while
            # adding the account to the system (not in Chrome), for some reason `type` is not set
            # so in that case we fall back to `public-key`
            # since that's the only option we support anyways
            challenge_response.setdefault("type", PublicKeyCredentialType.PUBLIC_KEY)

        try:
            credential = parse_authentication_credential_json(challenge_response)
        except InvalidJSONStructure as exc:
            LOGGER.warning("Invalid WebAuthn challenge response", exc=exc)
            raise ChallengeValidationError("Invalid device", "invalid") from None

        device = devices.filter(credential_id=credential.id).first()
        if not device:
            raise ChallengeValidationError("Invalid device", "invalid")

        # When a device_type was set when creating the device (2024.4+), and we have a limitation,
        # make sure the device type is allowed.
        if (
            device.device_type
            and self.validate_stage.webauthn_allowed_device_types.exists()
            and not self.validate_stage.webauthn_allowed_device_types.filter(
                pk=device.device_type.pk
            ).exists()
        ):
            raise ChallengeValidationError(
                _(
                    "Invalid device type. Contact your {brand} administrator for help.".format(
                        brand=self.request.brand.branding_title
                    )
                ),
                "invalid",
                failure_context=self._get_failure_context(device),
            )

        encoded_challenge = challenge["challenge"]
        challenge_bytes = urlsafe_b64decode(encoded_challenge + "=" * (-len(encoded_challenge) % 4))
        try:
            authentication_verification = verify_authentication_response(
                credential=credential,
                expected_challenge=challenge_bytes,
                expected_rp_id=get_rp_id(self.request),
                expected_origin=get_origin(self.request),
                credential_public_key=base64url_to_bytes(device.public_key),
                credential_current_sign_count=device.sign_count,
                require_user_verification=self.validate_stage.webauthn_user_verification
                == UserVerification.REQUIRED,
            )
        except InvalidAuthenticationResponse as exc:
            LOGGER.warning("Assertion failed", exc=exc)
            raise ChallengeValidationError(
                "Assertion failed", failure_context=self._get_failure_context(device)
            ) from exc

        with audit_ignore():
            device.set_sign_count(authentication_verification.new_sign_count)
        return device

    def _get_failure_context(self, device: WebAuthnDevice) -> dict:
        return {"device_type": device.device_type, "device": device}
