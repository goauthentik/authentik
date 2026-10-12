"""Trusted origins must work across ceremonies without weakening credential verification."""

from hashlib import sha256
from json import dumps

from cbor2 import dumps as cbor_encode
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from django.core.exceptions import ValidationError as ModelValidationError
from django.test import SimpleTestCase, TestCase
from rest_framework.exceptions import ValidationError
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url

from authentik.core.tests.utils import RequestFactory, create_test_user
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.views.executor import FlowExecutorView
from authentik.stages.authenticator_validate.api import AuthenticatorValidateStageSerializer
from authentik.stages.authenticator_validate.challenge import validate_challenge_webauthn
from authentik.stages.authenticator_validate.models import AuthenticatorValidateStage
from authentik.stages.authenticator_validate.stage import AuthenticatorValidateStageView
from authentik.stages.authenticator_webauthn.api.stages import AuthenticatorWebAuthnStageSerializer
from authentik.stages.authenticator_webauthn.models import (
    AuthenticatorWebAuthnStage,
    WebAuthnDevice,
)
from authentik.stages.authenticator_webauthn.stage import (
    PLAN_CONTEXT_WEBAUTHN_CHALLENGE,
    AuthenticatorWebAuthnChallengeResponse,
    AuthenticatorWebAuthnStageView,
)
from authentik.stages.authenticator_webauthn.utils import (
    get_expected_origins,
    validate_webauthn_origin,
)
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.identification.stage import (
    IdentificationChallengeResponse,
    IdentificationStageView,
)

ANDROID_ORIGIN = "android:apk-key-hash:" + bytes_to_base64url(sha256(b"app certificate").digest())
OTHER_ANDROID_ORIGIN = "android:apk-key-hash:" + bytes_to_base64url(sha256(b"other app").digest())
WEB_ORIGIN = "https://login.example.com"


class TestOriginValidation(SimpleTestCase):
    """Validate configuration through both model validators and the API fields."""

    def test_valid_origins(self):
        for origin in [ANDROID_ORIGIN, WEB_ORIGIN, "https://login.example.com:9443"]:
            with self.subTest(origin=origin):
                validate_webauthn_origin(origin)

    def test_invalid_origins(self):
        for origin in [
            "",
            "null",
            "*",
            "https://*.example.com",
            "http://example.com",
            "https://example.com:99999",
            "https://example.com:",
            "https://example.com/",
            "https://example.com/path",
            "https://example.com?",
            "https://example.com#",
            "https://user:password@example.com",
            "https://example.com\n",
            "android:apk-key-hash:*",
            ANDROID_ORIGIN + "=",
            "android:apk-key-hash:" + "A" * 42 + "B",
            OTHER_ANDROID_ORIGIN[:-1],
        ]:
            with self.subTest(origin=origin), self.assertRaises(ModelValidationError):
                validate_webauthn_origin(origin)

    def test_serializer_fields(self):
        for serializer, field_name in [
            (AuthenticatorWebAuthnStageSerializer, "additional_accepted_origins"),
            (AuthenticatorValidateStageSerializer, "webauthn_additional_accepted_origins"),
        ]:
            field = serializer().fields[field_name]
            with self.subTest(field=field_name):
                self.assertEqual(field.run_validation([]), [])
                self.assertEqual(
                    field.run_validation([ANDROID_ORIGIN, WEB_ORIGIN]), [ANDROID_ORIGIN, WEB_ORIGIN]
                )
                for value in [["*"], [""], ["http://example.com"], None, ANDROID_ORIGIN]:
                    with self.subTest(value=value), self.assertRaises(ValidationError):
                        field.run_validation(value)


class TestWebAuthnOrigins(TestCase):
    """Exercise the actual WebAuthn verifier with generated credentials and signatures."""

    def setUp(self):
        self.user = create_test_user()
        self.request = RequestFactory().get("/", secure=True)
        self.plan = FlowPlan("")
        self.plan.context[PLAN_CONTEXT_PENDING_USER] = self.user
        self.plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE] = b"test challenge" * 3
        self.registration_stage = AuthenticatorWebAuthnStage.objects.create(name="registration")
        self.validation_stage = AuthenticatorValidateStage.objects.create(name="validation")
        self.private_key = Ed25519PrivateKey.generate()
        self.public_key = cbor_encode(
            {
                1: 1,
                3: -8,
                -1: 6,
                -2: self.private_key.public_key().public_bytes_raw(),
            }
        )
        self.credential_id = b"test credential"

    def credential(
        self, origin, *, registration=False, rp_id="testserver", challenge=None, user_verified=True
    ):
        """Build none-attested registrations or signed assertions for the test credential."""
        client_data = dumps(
            {
                "type": "webauthn.create" if registration else "webauthn.get",
                "origin": origin,
                "challenge": bytes_to_base64url(
                    challenge or self.plan.context[PLAN_CONTEXT_WEBAUTHN_CHALLENGE]
                ),
                "crossOrigin": False,
            }
        ).encode()
        flags = 0x01 | (0x04 if user_verified else 0) | (0x40 if registration else 0)
        auth_data = sha256(rp_id.encode()).digest() + bytes([flags]) + (1).to_bytes(4, "big")
        response = {"clientDataJSON": bytes_to_base64url(client_data)}
        if registration:
            auth_data += bytes(16) + len(self.credential_id).to_bytes(2, "big")
            auth_data += self.credential_id + self.public_key
            response["attestationObject"] = bytes_to_base64url(
                cbor_encode(
                    {
                        "fmt": "none",
                        "attStmt": {},
                        "authData": auth_data,
                    }
                )
            )
        else:
            response["authenticatorData"] = bytes_to_base64url(auth_data)
            response["signature"] = bytes_to_base64url(
                self.private_key.sign(auth_data + sha256(client_data).digest())
            )
        return {
            "id": bytes_to_base64url(self.credential_id),
            "rawId": bytes_to_base64url(self.credential_id),
            "type": "public-key",
            "response": response,
        }

    def register(self, origin, **kwargs):
        stage_view = AuthenticatorWebAuthnStageView(
            FlowExecutorView(current_stage=self.registration_stage, plan=self.plan),
            request=self.request,
        )
        response = AuthenticatorWebAuthnChallengeResponse(stage=stage_view)
        response.request = self.request
        return response.validate_response(self.credential(origin, registration=True, **kwargs))

    def create_device(self):
        return WebAuthnDevice.objects.create(
            user=self.user,
            credential_id=bytes_to_base64url(self.credential_id),
            public_key=bytes_to_base64url(self.public_key),
            rp_id="testserver",
            sign_count=0,
        )

    def authenticate(self, credential, *, stage=None):
        stage_view = AuthenticatorValidateStageView(
            FlowExecutorView(current_stage=stage or self.validation_stage, plan=self.plan),
            request=self.request,
        )
        return validate_challenge_webauthn(credential, stage_view, self.user)

    def test_request_origin_preserved(self):
        self.request.META["HTTP_ORIGIN"] = "https://untrusted.example.com"
        additional = [ANDROID_ORIGIN, "https://testserver", ANDROID_ORIGIN]
        self.assertEqual(
            get_expected_origins(self.request, additional), ["https://testserver", ANDROID_ORIGIN]
        )
        self.assertEqual(len(additional), 3)
        self.assertEqual(get_expected_origins(self.request, []), ["https://testserver"])

    def test_configuration_round_trip(self):
        for serializer_class, stage, field_name in [
            (
                AuthenticatorWebAuthnStageSerializer,
                self.registration_stage,
                "additional_accepted_origins",
            ),
            (
                AuthenticatorValidateStageSerializer,
                self.validation_stage,
                "webauthn_additional_accepted_origins",
            ),
        ]:
            with self.subTest(field=field_name):
                self.assertEqual(serializer_class(stage).data[field_name], [])
                for origins in [[ANDROID_ORIGIN, WEB_ORIGIN], []]:
                    serializer = serializer_class(stage, data={field_name: origins}, partial=True)
                    self.assertTrue(serializer.is_valid(), serializer.errors)
                    serializer.save()
                    stage.refresh_from_db()
                    self.assertEqual(serializer_class(stage).data[field_name], origins)

    def test_registration_origins(self):
        for allowed in [[], [WEB_ORIGIN, ANDROID_ORIGIN, OTHER_ANDROID_ORIGIN]]:
            self.registration_stage.additional_accepted_origins = allowed
            for origin in [
                "https://testserver",
                ANDROID_ORIGIN,
                OTHER_ANDROID_ORIGIN,
                WEB_ORIGIN,
                "https://untrusted.example.com",
                ANDROID_ORIGIN.lower(),
            ]:
                with self.subTest(allowed=allowed, origin=origin):
                    if origin == "https://testserver" or origin in allowed:
                        self.assertEqual(
                            self.register(origin).registration.credential_id, self.credential_id
                        )
                    else:
                        with self.assertRaises(ValidationError):
                            self.register(origin)

    def test_registration_checks_preserved(self):
        self.registration_stage.additional_accepted_origins = [ANDROID_ORIGIN]
        for kwargs in [{"rp_id": "other.example.com"}, {"challenge": b"wrong challenge"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                self.register(ANDROID_ORIGIN, **kwargs)

    def test_authentication_origins(self):
        device = self.create_device()
        for allowed in [[], [WEB_ORIGIN, ANDROID_ORIGIN, OTHER_ANDROID_ORIGIN]]:
            self.validation_stage.webauthn_additional_accepted_origins = allowed
            for origin in [
                "https://testserver",
                ANDROID_ORIGIN,
                OTHER_ANDROID_ORIGIN,
                WEB_ORIGIN,
                "https://untrusted.example.com",
                ANDROID_ORIGIN.lower(),
            ]:
                device.set_sign_count(0)
                with self.subTest(allowed=allowed, origin=origin):
                    if origin == "https://testserver" or origin in allowed:
                        verified = self.authenticate(self.credential(origin))
                        self.assertEqual(verified.pk, device.pk)
                        self.assertEqual(verified.sign_count, 1)
                    else:
                        with self.assertRaises(ValidationError):
                            self.authenticate(self.credential(origin))

    def test_authentication_checks_preserved(self):
        device = self.create_device()
        self.validation_stage.webauthn_additional_accepted_origins = [ANDROID_ORIGIN]
        self.validation_stage.webauthn_user_verification = "required"
        for kwargs in [
            {"rp_id": "other.example.com"},
            {"challenge": b"wrong challenge"},
            {"user_verified": False},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                self.authenticate(self.credential(ANDROID_ORIGIN, **kwargs))
        credential = self.credential(ANDROID_ORIGIN)
        credential["response"]["signature"] = bytes_to_base64url(bytes(64))
        with self.assertRaises(ValidationError):
            self.authenticate(credential)
        device.refresh_from_db()
        self.assertEqual(device.sign_count, 0)

    def test_stage_isolation(self):
        self.registration_stage.additional_accepted_origins = [ANDROID_ORIGIN]
        self.registration_stage.save()
        self.create_device()
        with self.assertRaises(ValidationError):
            self.authenticate(self.credential(ANDROID_ORIGIN))
        self.validation_stage.webauthn_additional_accepted_origins = [ANDROID_ORIGIN]
        self.validation_stage.save()
        other = AuthenticatorValidateStage.objects.create(name="other validation")
        with self.assertRaises(ValidationError):
            self.authenticate(self.credential(ANDROID_ORIGIN), stage=other)
        self.authenticate(self.credential(ANDROID_ORIGIN))

    def test_identification_uses_referenced_validation_stage(self):
        device = self.create_device()
        identification = IdentificationStage.objects.create(
            name="identification",
            user_fields=["username"],
            webauthn_stage=self.validation_stage,
        )
        stage_view = IdentificationStageView(
            FlowExecutorView(current_stage=identification, plan=self.plan),
            request=self.request,
        )
        response = IdentificationChallengeResponse(stage=stage_view)
        with self.assertRaises(ValidationError):
            response._validate_passkey_response(self.credential(ANDROID_ORIGIN))
        self.validation_stage.webauthn_additional_accepted_origins = [ANDROID_ORIGIN]
        self.validation_stage.save()
        self.assertEqual(
            response._validate_passkey_response(self.credential(ANDROID_ORIGIN)).pk, device.pk
        )
