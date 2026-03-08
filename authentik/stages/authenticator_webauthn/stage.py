"""WebAuthn stage"""

from dataclasses import dataclass
from uuid import UUID

from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import load_der_x509_certificate
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.http.request import QueryDict
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import CharField
from rest_framework.serializers import ValidationError
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url
from webauthn.helpers.exceptions import WebAuthnException
from webauthn.helpers.options_to_json_dict import options_to_json_dict
from webauthn.helpers.parse_attestation_object import parse_attestation_object
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
from authentik.crypto.models import fingerprint_sha256
from authentik.flows.challenge import (
    Challenge,
    ChallengeResponse,
    WithUserInfoChallenge,
)
from authentik.flows.stage import ChallengeStageView
from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    AuthenticatorWebAuthnStage,
    WebAuthnDevice,
    WebAuthnDeviceType,
)
from authentik.stages.authenticator_webauthn.utils import get_origin, get_rp_id

PLAN_CONTEXT_WEBAUTHN_CHALLENGE = "goauthentik.io/stages/authenticator_webauthn/challenge"
PLAN_CONTEXT_WEBAUTHN_ATTEMPT = "goauthentik.io/stages/authenticator_webauthn/attempt"


@dataclass
class VerifiedRegistrationData:
    registration: VerifiedRegistration
    exists_query: Q
    attest_cert: str | None = None
    attest_cert_fingerprint: str | None = None


class AuthenticatorWebAuthnChallenge(WithUserInfoChallenge):
    """WebAuthn Challenge"""

    registration = JSONDictField()
    component = CharField(default="ak-stage-authenticator-webauthn")


class AuthenticatorWebAuthnChallengeResponse(ChallengeResponse):
    """WebAuthn Challenge response"""

    response = JSONDictField()
    component = CharField(default="ak-stage-authenticator-webauthn")

    request: HttpRequest
    user: User

    def validate_response(self, response: dict) -> VerifiedRegistrationData:
        """Validate webauthn challenge response"""
        challenge = self.stage.executor.plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE]

        try:
            registration: VerifiedRegistration = verify_registration_response(
                credential=response,
                expected_challenge=challenge,
                expected_rp_id=get_rp_id(self.request),
                expected_origin=get_origin(self.request),
            )
        except WebAuthnException as exc:
            self.stage.logger.warning("registration failed", exc=exc)
            raise ValidationError(f"Registration failed. Error: {exc}") from None

        registration_data = VerifiedRegistrationData(
            registration,
            exists_query=Q(credential_id=bytes_to_base64url(registration.credential_id)),
        )

        att_stmt = parse_attestation_object(registration.attestation_object).att_stmt
        if att_stmt.x5c and len(att_stmt.x5c) > 0:
            cert = load_der_x509_certificate(att_stmt.x5c[0])
            registration_data.attest_cert = cert.public_bytes(
                encoding=Encoding.PEM,
            ).decode("utf-8")
            registration_data.attest_cert_fingerprint = fingerprint_sha256(cert)
            registration_data.exists_query |= Q(
                attestation_certificate_fingerprint=registration_data.attest_cert_fingerprint
            )

        credential_id_exists = WebAuthnDevice.objects.filter(registration_data.exists_query).first()
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
                return registration_data
            # Otherwise just check if the given aaguid is in the allowed aaguids
            if UUID(aaguid) not in allowed_aaguids:
                raise invalid_error
        return registration_data


class AuthenticatorWebAuthnStageView(ChallengeStageView):
    """WebAuthn stage"""

    response_class = AuthenticatorWebAuthnChallengeResponse

    def get_challenge(self, *args, **kwargs) -> Challenge:
        stage: AuthenticatorWebAuthnStage = self.executor.current_stage
        self.executor.plan.context.setdefault(PLAN_CONTEXT_WEBAUTHN_ATTEMPT, 0)
        # clear flow variables prior to starting a new registration
        self.executor.plan.context.pop(PLAN_CONTEXT_WEBAUTHN_CHALLENGE, None)
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

        self.executor.plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = registration_options.challenge
        return AuthenticatorWebAuthnChallenge(
            data={
                "registration": options_to_json_dict(registration_options),
            }
        )

    def get_response_instance(self, data: QueryDict) -> AuthenticatorWebAuthnChallengeResponse:
        response: AuthenticatorWebAuthnChallengeResponse = super().get_response_instance(data)
        response.request = self.request
        response.user = self.get_pending_user()
        return response

    def challenge_invalid(self, response):
        stage: AuthenticatorWebAuthnStage = self.executor.current_stage
        self.executor.plan.context.setdefault(PLAN_CONTEXT_WEBAUTHN_ATTEMPT, 0)
        self.executor.plan.context[PLAN_CONTEXT_WEBAUTHN_ATTEMPT] += 1
        if (
            stage.max_attempts > 0
            and self.executor.plan.context[PLAN_CONTEXT_WEBAUTHN_ATTEMPT] >= stage.max_attempts
        ):
            return self.executor.stage_invalid(
                __(
                    "Exceeded maximum attempts. "
                    "Contact your {brand} administrator for help.".format(
                        brand=self.request.brand.branding_title
                    )
                )
            )
        return super().challenge_invalid(response)

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        # Webauthn Challenge has already been validated
        webauthn_credential: VerifiedRegistrationData = response.validated_data["response"]
        existing_device = WebAuthnDevice.objects.filter(webauthn_credential.exists_query).first()
        if not existing_device:
            name = "WebAuthn Device"
            device_type = WebAuthnDeviceType.objects.filter(
                aaguid=webauthn_credential.registration.aaguid
            ).first()
            if device_type and device_type.description:
                name = device_type.description
            WebAuthnDevice.objects.create(
                name=name,
                user=self.get_pending_user(),
                public_key=bytes_to_base64url(
                    webauthn_credential.registration.credential_public_key
                ),
                credential_id=bytes_to_base64url(webauthn_credential.registration.credential_id),
                sign_count=webauthn_credential.registration.sign_count,
                rp_id=get_rp_id(self.request),
                device_type=device_type,
                aaguid=webauthn_credential.registration.aaguid,
                attestation_certificate_pem=webauthn_credential.attest_cert,
                attestation_certificate_fingerprint=webauthn_credential.attest_cert_fingerprint,
            )
        else:
            return self.executor.stage_invalid("Device with Credential ID already exists.")
        return self.executor.stage_ok()
