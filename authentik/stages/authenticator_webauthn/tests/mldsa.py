"""Helpers to build WebAuthn responses signed with a generated ML-DSA (FIPS 204) key.

No shipping authenticator implements ML-DSA yet, so these construct the same CBOR structures a
CTAP2 authenticator would return, using python-fido2's encoders and a key from cryptography."""

from hashlib import sha256
from json import dumps
from os import urandom

from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA44PrivateKey
from fido2 import cbor
from fido2.cose import MLDSA44
from fido2.webauthn import AttestationObject, AttestedCredentialData, AuthenticatorData
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url

from authentik.stages.authenticator_webauthn.models import UNKNOWN_DEVICE_TYPE_AAGUID


def _client_data(webauthn_type: str, challenge: bytes, origin: str) -> bytes:
    return dumps(
        {
            "type": webauthn_type,
            "challenge": bytes_to_base64url(challenge),
            "origin": origin,
            "crossOrigin": False,
        }
    ).encode("utf-8")


class MLDSACredential:
    """A software ML-DSA-44 credential that can produce registration and assertion responses"""

    def __init__(self, rp_id: str, origin: str):
        self.rp_id = rp_id
        self.origin = origin
        self.private_key = MLDSA44PrivateKey.generate()
        self.credential_id = urandom(32)
        self.sign_count = 0

    @property
    def cose_public_key(self) -> bytes:
        """CBOR-encoded COSE public key, as stored on a WebAuthnDevice"""
        return cbor.encode(MLDSA44.from_cryptography_key(self.private_key.public_key()))

    def registration_response(self, challenge: bytes) -> dict:
        """Build a `navigator.credentials.create()` response with a `none` attestation"""
        credential_data = AttestedCredentialData.create(
            bytes.fromhex(UNKNOWN_DEVICE_TYPE_AAGUID.replace("-", "")),
            self.credential_id,
            MLDSA44.from_cryptography_key(self.private_key.public_key()),
        )
        auth_data = AuthenticatorData.create(
            sha256(self.rp_id.encode("utf-8")).digest(),
            AuthenticatorData.FLAG.UP | AuthenticatorData.FLAG.UV | AuthenticatorData.FLAG.AT,
            self.sign_count,
            credential_data,
        )
        attestation = AttestationObject.create("none", auth_data, {})
        return {
            "id": bytes_to_base64url(self.credential_id),
            "rawId": bytes_to_base64url(self.credential_id),
            "type": "public-key",
            "registrationClientExtensions": "{}",
            "response": {
                "clientDataJSON": bytes_to_base64url(
                    _client_data("webauthn.create", challenge, self.origin)
                ),
                "attestationObject": bytes_to_base64url(bytes(attestation)),
            },
        }

    def assertion_response(self, challenge: bytes) -> dict:
        """Build a `navigator.credentials.get()` response signed with the ML-DSA key"""
        self.sign_count += 1
        auth_data = AuthenticatorData.create(
            sha256(self.rp_id.encode("utf-8")).digest(),
            AuthenticatorData.FLAG.UP | AuthenticatorData.FLAG.UV,
            self.sign_count,
        )
        client_data = _client_data("webauthn.get", challenge, self.origin)
        signature = self.private_key.sign(bytes(auth_data) + sha256(client_data).digest())
        return {
            "id": bytes_to_base64url(self.credential_id),
            "rawId": bytes_to_base64url(self.credential_id),
            "type": "public-key",
            "assertionClientExtensions": "{}",
            "response": {
                "clientDataJSON": bytes_to_base64url(client_data),
                "authenticatorData": bytes_to_base64url(bytes(auth_data)),
                "signature": bytes_to_base64url(signature),
                "userHandle": None,
            },
        }
