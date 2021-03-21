"""WebAuthn stage"""

from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from rest_framework.fields import JSONField
from rest_framework.serializers import ValidationError
from structlog.stdlib import get_logger
from webauthn.webauthn import (
    RegistrationRejectedException,
    WebAuthnCredential,
    WebAuthnMakeCredentialOptions,
    WebAuthnRegistrationResponse,
)

from authentik.core.models import User
from authentik.flows.challenge import Challenge, ChallengeResponse, ChallengeTypes
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice
from authentik.stages.authenticator_webauthn.utils import (
    generate_challenge,
    get_origin,
    get_rp_id,
)

RP_NAME = "authentik"

LOGGER = get_logger()

SESSION_KEY_WEBAUTHN_AUTHENTICATED = (
    "authentik_stages_authenticator_webauthn_authenticated"
)


class AuthenticatorWebAuthnChallenge(Challenge):
    """WebAuthn Challenge"""

    registration = JSONField()


class AuthenticatorWebAuthnChallengeResponse(ChallengeResponse):
    """WebAuthn Challenge response"""

    response = JSONField()

    request: HttpRequest
    user: User

    def validate_response(self, response: dict) -> dict:
        """Validate webauthn challenge response"""
        challenge = self.request.session["challenge"]

        trusted_attestation_cert_required = True
        self_attestation_permitted = True
        none_attestation_permitted = True

        webauthn_registration_response = WebAuthnRegistrationResponse(
            get_rp_id(self.request),
            get_origin(self.request),
            response,
            challenge,
            trusted_attestation_cert_required=trusted_attestation_cert_required,
            self_attestation_permitted=self_attestation_permitted,
            none_attestation_permitted=none_attestation_permitted,
            uv_required=False,
        )  # User Verification

        try:
            webauthn_credential = webauthn_registration_response.verify()
        except RegistrationRejectedException as exc:
            LOGGER.warning("registration failed", exc=exc)
            raise ValidationError("Registration failed. Error: {}".format(exc))

        # Step 17.
        #
        # Check that the credentialId is not yet registered to any other user.
        # If registration is requested for a credential that is already registered
        # to a different user, the Relying Party SHOULD fail this registration
        # ceremony, or it MAY decide to accept the registration, e.g. while deleting
        # the older registration.
        credential_id_exists = WebAuthnDevice.objects.filter(
            credential_id=webauthn_credential.credential_id
        ).first()
        if credential_id_exists:
            raise ValidationError("Credential ID already exists.")

        webauthn_credential.credential_id = str(
            webauthn_credential.credential_id, "utf-8"
        )
        webauthn_credential.public_key = str(webauthn_credential.public_key, "utf-8")

        return webauthn_credential


class AuthenticatorWebAuthnStageView(ChallengeStageView):
    """WebAuthn stage"""

    response_class = AuthenticatorWebAuthnChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        # clear session variables prior to starting a new registration
        self.request.session.pop("challenge", None)

        challenge = generate_challenge(32)

        # We strip the saved challenge of padding, so that we can do a byte
        # comparison on the URL-safe-without-padding challenge we get back
        # from the browser.
        # We will still pass the padded version down to the browser so that the JS
        # can decode the challenge into binary without too much trouble.
        self.request.session["challenge"] = challenge.rstrip("=")
        user = self.get_pending_user()
        make_credential_options = WebAuthnMakeCredentialOptions(
            challenge,
            RP_NAME,
            get_rp_id(self.request),
            user.uid,
            user.username,
            user.name,
            user.avatar,
        )

        registration_dict = make_credential_options.registration_dict
        registration_dict["authenticatorSelection"] = {
            "requireResidentKey": False,
            "userVerification": "preferred",
        }

        return AuthenticatorWebAuthnChallenge(
            data={
                "type": ChallengeTypes.native.value,
                "component": "ak-stage-authenticator-webauthn",
                "registration": registration_dict,
            }
        )

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        user = self.executor.plan.context.get(PLAN_CONTEXT_PENDING_USER)
        if not user:
            LOGGER.debug("No pending user, continuing")
            return self.executor.stage_ok()
        return super().get(request, *args, **kwargs)

    def get_response_instance(
        self, data: QueryDict
    ) -> AuthenticatorWebAuthnChallengeResponse:
        response: AuthenticatorWebAuthnChallengeResponse = (
            super().get_response_instance(data)
        )
        response.request = self.request
        response.user = self.get_pending_user()
        return response

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        # Webauthn Challenge has already been validated
        webauthn_credential: WebAuthnCredential = response.validated_data["response"]
        existing_device = WebAuthnDevice.objects.filter(
            credential_id=webauthn_credential.credential_id
        ).first()
        if not existing_device:
            WebAuthnDevice.objects.create(
                user=self.get_pending_user(),
                public_key=webauthn_credential.public_key,
                credential_id=webauthn_credential.credential_id,
                sign_count=webauthn_credential.sign_count,
                rp_id=get_rp_id(self.request),
            )
        else:
            return self.executor.stage_invalid(
                "Device with Credential ID already exists."
            )
        return self.executor.stage_ok()
