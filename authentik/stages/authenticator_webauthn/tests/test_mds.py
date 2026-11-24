"""MDS blob parsing tests"""

from base64 import b64encode
from datetime import UTC, datetime, timedelta
from json import dumps, loads

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import NameOID
from django.test import TestCase
from fido2.utils import websafe_decode, websafe_encode

from authentik.stages.authenticator_webauthn.tasks import (
    MDS_BLOB_PATH,
    MDS_STATEMENT_LIST_DEFAULTS,
    parse_mds_blob,
)


def _certificate(
    subject: str, key: rsa.RSAPrivateKey, issuer: str, issuer_key: rsa.RSAPrivateKey, ca: bool
) -> x509.Certificate:
    now = datetime.now(UTC)
    return (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)]))
        .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, issuer)]))
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
        .sign(issuer_key, hashes.SHA256())
    )


class TestMDSParsing(TestCase):
    """MDS blob parsing tests"""

    def test_statement_without_optional_lists(self):
        """A signed blob whose statement omits userVerificationDetails and attachmentHint"""
        with open(MDS_BLOB_PATH, mode="rb") as raw_blob:
            bundled_payload = loads(websafe_decode(raw_blob.read().split(b".")[1]))

        entry = next(
            entry
            for entry in bundled_payload["entries"]
            if entry.get("aaguid") and entry.get("metadataStatement")
        )
        for key in MDS_STATEMENT_LIST_DEFAULTS:
            entry["metadataStatement"].pop(key, None)
        payload = {**bundled_payload, "entries": [entry]}

        root_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        leaf_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        root = _certificate(
            "authentik test MDS root", root_key, "authentik test MDS root", root_key, True
        )
        leaf = _certificate(
            "authentik test MDS signer", leaf_key, "authentik test MDS root", root_key, False
        )

        header = {
            "alg": "RS256",
            "typ": "JWT",
            "x5c": [b64encode(leaf.public_bytes(serialization.Encoding.DER)).decode()],
        }
        message = b".".join(
            websafe_encode(dumps(part).encode()).encode() for part in (header, payload)
        )
        signature = leaf_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
        blob = message + b"." + websafe_encode(signature).encode()

        parsed = parse_mds_blob(blob, root.public_bytes(serialization.Encoding.DER))

        self.assertEqual(len(parsed.entries), 1)
        statement = parsed.entries[0].metadata_statement
        self.assertEqual(statement.user_verification_details, [])
        self.assertEqual(statement.attachment_hint, [])
        self.assertEqual(str(parsed.entries[0].aaguid), entry["aaguid"])
