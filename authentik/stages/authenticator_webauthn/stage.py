"""WebAuthn stage"""
from json import dumps, loads

from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from rest_framework.fields import CharField, JSONField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger
from webauthn import generate_registration_options, options_to_json, verify_registration_response
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.exceptions import InvalidRegistrationResponse
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialCreationOptions,
    RegistrationCredential,
)
from webauthn.registration.verify_registration_response import VerifiedRegistration

from authentik.core.models import User
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    ChallengeTypes,
    WithUserInfoChallenge,
)
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_webauthn.models import AuthenticateWebAuthnStage, WebAuthnDevice
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id

LOGGER = get_logger()

SESSION_KEY_WEBAUTHN_AUTHENTICATED = "authentik_stages_authenticator_webauthn_authenticated"


class AuthenticatorWebAuthnChallenge(WithUserInfoChallenge):
    """WebAuthn Challenge"""

    registration = JSONField()
    component = CharField(default="ak-stage-authenticator-webauthn")


class AuthenticatorWebAuthnChallengeResponse(ChallengeResponse):
    """WebAuthn Challenge response"""

    response = JSONField()
    component = CharField(default="ak-stage-authenticator-webauthn")

    request: HttpRequest
    user: User

    def validate_response(self, response: dict) -> dict:
        """Validate webauthn challenge response"""
        challenge = self.request.session["challenge"]

        try:
            registration: VerifiedRegistration = verify_registration_response(
                credential=RegistrationCredential.parse_raw(dumps(response)),
                expected_challenge=challenge,
                expected_rp_id=get_rp_id(self.request),
                expected_origin=get_origin(self.request),
            )
        except InvalidRegistrationResponse as exc:
            LOGGER.warning("registration failed", exc=exc)
            raise ValidationError(f"Registration failed. Error: {exc}")

        credential_id_exists = WebAuthnDevice.objects.filter(
            credential_id=bytes_to_base64url(registration.credential_id)
        ).first()
        if credential_id_exists:
            raise ValidationError("Credential ID already exists.")

        return registration


class AuthenticatorWebAuthnStageView(ChallengeStageView):
    """WebAuthn stage"""

    response_class = AuthenticatorWebAuthnChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        # clear session variables prior to starting a new registration
        self.request.session.pop("challenge", None)
        stage: AuthenticateWebAuthnStage = self.executor.current_stage
        user = self.get_pending_user()

        # library accepts none so we store null in the database, but if there is a value
        # set, cast it to string to ensure it's not a django class
        authenticator_attachment = stage.authenticator_attachment
        if authenticator_attachment:
            authenticator_attachment = str(authenticator_attachment)

        registration_options: PublicKeyCredentialCreationOptions = generate_registration_options(
            rp_id=get_rp_id(self.request),
            rp_name=self.request.tenant.branding_title,
            user_id=user.uid,
            user_name=user.username,
            user_display_name=user.name,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=str(stage.resident_key_requirement),
                user_verification=str(stage.user_verification),
                authenticator_attachment=authenticator_attachment,
            ),
        )

        self.request.session["challenge"] = registration_options.challenge
        self.request.session.save()
        return AuthenticatorWebAuthnChallenge(
            data={
                "type": ChallengeTypes.NATIVE.value,
                "registration": loads(options_to_json(registration_options)),
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

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
            WebAuthnDevice.objects.create(
                user=self.get_pending_user(),
                public_key=bytes_to_base64url(webauthn_credential.credential_public_key),
                credential_id=bytes_to_base64url(webauthn_credential.credential_id),
                sign_count=webauthn_credential.sign_count,
                rp_id=get_rp_id(self.request),
                name="WebAuthn Device",
            )
        else:
            return self.executor.stage_invalid("Device with Credential ID already exists.")
        return self.executor.stage_ok()
