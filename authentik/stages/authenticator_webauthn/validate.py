from json import loads

from django.http import HttpRequest
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError
from webauthn import options_to_json
from webauthn.authentication.generate_authentication_options import generate_authentication_options
from webauthn.authentication.verify_authentication_response import verify_authentication_response
from webauthn.helpers.base64url_to_bytes import base64url_to_bytes
from webauthn.helpers.exceptions import InvalidAuthenticationResponse
from webauthn.helpers.structs import UserVerificationRequirement

from authentik.core.api.utils import JSONDictField
from authentik.core.signals import login_failed
from authentik.flows.challenge import Challenge, ChallengeTypes
from authentik.stages.authenticator.validate import (
    DeviceChallenge,
    DeviceChallengeResponse,
    DeviceValidator,
)
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage, DeviceClasses
from authentik.stages.authenticator_webauthn.models import UserVerification, WebAuthnDevice
from authentik.stages.authenticator_webauthn.stage import SESSION_KEY_WEBAUTHN_CHALLENGE
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id


class WebAuthnDeviceChallenge(DeviceChallenge):
    component = CharField(default="ak-stage-authenticator-validate-device-webauthn")
    data = JSONDictField()


class WebAuthnDeviceChallengeResponse(DeviceChallengeResponse[WebAuthnDevice]):
    component = CharField(default="ak-stage-authenticator-validate-device-webauthn")
    data = JSONDictField()

    def validate_data(self, data: dict) -> dict:
        request = self.stage.request

        challenge = request.session.get(SESSION_KEY_WEBAUTHN_CHALLENGE)
        credential_id = data.get("id")

        device = WebAuthnDevice.objects.filter(credential_id=credential_id).first()
        if not device:
            raise ValidationError("Invalid device")
        # We can only check the device's user if the user we're given isn't anonymous
        # as this validation is also used for password-less login where webauthn is the very first
        # step done by a user. Only if this validation happens at a later stage we can check
        # that the device belongs to the user
        user = self.stage.get_pending_user()
        if not user.is_anonymous and device.user != user:
            raise ValidationError("Invalid device")

        stage: AuthenticatorValidateStage = self.stage.executor.current_stage

        try:
            authentication_verification = verify_authentication_response(
                credential=data,
                expected_challenge=challenge,
                expected_rp_id=get_rp_id(request),
                expected_origin=get_origin(request),
                credential_public_key=base64url_to_bytes(device.public_key),
                credential_current_sign_count=device.sign_count,
                require_user_verification=stage.webauthn_user_verification
                == UserVerification.REQUIRED,
            )
        except InvalidAuthenticationResponse as exc:
            self.stage.logger.warning("Assertion failed", exc=exc)
            login_failed.send(
                sender=__name__,
                credentials={"username": user.username},
                request=self.stage.request,
                stage=self.stage.executor.current_stage,
                device=device,
                device_class=DeviceClasses.WEBAUTHN.value,
            )
            raise ValidationError("Assertion failed") from exc
        device.set_sign_count(authentication_verification.new_sign_count)
        return data


class WebAuthnDeviceValidator(DeviceValidator[WebAuthnDevice]):
    response_class = WebAuthnDeviceChallengeResponse

    @staticmethod
    def get_webauthn_challenge_without_user(
        request: HttpRequest, user_verification: UserVerification
    ) -> WebAuthnDeviceChallenge:
        """Same as `get_webauthn_challenge`, but allows any client device. We can then later check
        who the device belongs to."""
        request.session.pop(SESSION_KEY_WEBAUTHN_CHALLENGE, None)
        authentication_options = generate_authentication_options(
            rp_id=get_rp_id(request),
            allow_credentials=[],
            user_verification=user_verification,
        )
        request.session[SESSION_KEY_WEBAUTHN_CHALLENGE] = authentication_options.challenge

        webauthn_data = loads(options_to_json(authentication_options))
        challenge = WebAuthnDeviceChallenge(
            data={
                # "device_class": DeviceClasses.WEBAUTHN,
                # "device_uid": -1,
                "data": webauthn_data,
            }
        )
        challenge.is_valid()
        return challenge

    def get_challenge(self, *args, **kwargs) -> Challenge:
        self.request.session.pop(SESSION_KEY_WEBAUTHN_CHALLENGE, None)

        allowed_credentials = []

        if self.device:
            # We want all the user's WebAuthn devices and merge their challenges
            for user_device in WebAuthnDevice.objects.filter(user=self.device.user).order_by(
                "name"
            ):
                user_device: WebAuthnDevice
                allowed_credentials.append(user_device.descriptor)

        authentication_options = generate_authentication_options(
            rp_id=get_rp_id(self.request),
            allow_credentials=allowed_credentials,
            user_verification=UserVerificationRequirement(
                self.executor.current_stage.webauthn_user_verification
            ),
        )

        self.request.session[SESSION_KEY_WEBAUTHN_CHALLENGE] = authentication_options.challenge

        return WebAuthnDeviceChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "data": loads(options_to_json(authentication_options)),
            }
        )
