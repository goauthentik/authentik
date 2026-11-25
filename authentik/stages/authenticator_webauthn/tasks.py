"""MDS Helpers"""

from base64 import b64decode
from functools import lru_cache
from json import loads
from pathlib import Path

from cryptography import x509
from django.core.cache import cache
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from dramatiq.actor import actor
from fido2.attestation import verify_x509_chain
from fido2.cose import CoseKey
from fido2.mds3 import MetadataBlobPayload, filter_revoked
from fido2.utils import websafe_decode

from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    WebAuthnDeviceType,
)
from authentik.tasks.middleware import CurrentTask

CACHE_KEY_MDS_NO = "goauthentik.io/stages/authenticator_webauthn/mds_no"
AAGUID_BLOB_PATH = Path(__file__).parent / "mds" / "aaguid.json"
MDS_BLOB_PATH = Path(__file__).parent / "mds" / "blob.jwt"
MDS_CA_PATH = Path(__file__).parent / "mds" / "root-r3.crt"


@lru_cache
def mds_ca() -> bytes:
    """Cache MDS Signature CA, GlobalSign Root CA - R3"""
    with open(MDS_CA_PATH, mode="rb") as _raw_root:
        return _raw_root.read()


# fido2 requires these, but the FIDO Alliance publishes some statements without them.
# Fixed upstream in fido2 2.2.2; switch back to fido2.mds3.parse_blob once it is released.
MDS_STATEMENT_LIST_DEFAULTS = ("userVerificationDetails", "attachmentHint")


def parse_mds_blob(blob: bytes, trust_root: bytes) -> MetadataBlobPayload:
    """Verify an MDS3 blob's signature and parse it, tolerating statements without
    `userVerificationDetails` or `attachmentHint`."""
    message, signature_b64 = blob.rsplit(b".", 1)
    header, payload = (loads(websafe_decode(part)) for part in message.split(b"."))

    chain = [b64decode(cert) for cert in header.get("x5c", [])] + [trust_root]
    verify_x509_chain(chain)
    leaf = x509.load_der_x509_certificate(chain[0])
    public_key = CoseKey.for_name(header["alg"]).from_cryptography_key(leaf.public_key())
    public_key.verify(message, websafe_decode(signature_b64))

    for entry in payload.get("entries", []):
        statement = entry.get("metadataStatement")
        if statement is None:
            continue
        for key in MDS_STATEMENT_LIST_DEFAULTS:
            if statement.get(key) is None:
                statement[key] = []

    return MetadataBlobPayload.from_dict(payload)


@actor(description=_("Background task to import FIDO Alliance MDS blob and AAGUIDs into database."))
def webauthn_mds_import(force=False):
    """Background task to import FIDO Alliance MDS blob and AAGUIDs into database"""
    self = CurrentTask.get_task()
    with open(MDS_BLOB_PATH, mode="rb") as _raw_blob:
        blob = parse_mds_blob(_raw_blob.read(), mds_ca())
    to_create_update = [
        WebAuthnDeviceType(
            aaguid=UNKNOWN_DEVICE_TYPE_AAGUID,
            description="authentik: Unknown devices",
        )
    ]
    to_delete = []

    mds_no = cache.get(CACHE_KEY_MDS_NO)
    if mds_no != blob.no or force:
        for entry in blob.entries:
            aaguid = entry.aaguid
            if not aaguid:
                continue
            if not filter_revoked(entry):
                to_delete.append(str(aaguid))
                continue
            metadata = entry.metadata_statement
            to_create_update.append(
                WebAuthnDeviceType(
                    aaguid=str(aaguid),
                    description=metadata.description,
                    icon=metadata.icon,
                )
            )
    with atomic():
        WebAuthnDeviceType.objects.bulk_create(
            to_create_update,
            update_conflicts=True,
            update_fields=["description", "icon"],
            unique_fields=["aaguid"],
        )
        WebAuthnDeviceType.objects.filter(aaguid__in=to_delete).delete()
    if mds_no != blob.no:
        cache.set(CACHE_KEY_MDS_NO, blob.no)

    with open(AAGUID_BLOB_PATH, mode="rb") as _raw_blob:
        entries = loads(_raw_blob.read())
    to_create_update = [
        WebAuthnDeviceType(
            aaguid=str(aaguid), description=details.get("name"), icon=details.get("icon_light")
        )
        for aaguid, details in entries.items()
    ]
    with atomic():
        WebAuthnDeviceType.objects.bulk_create(
            to_create_update,
            update_conflicts=True,
            update_fields=["description", "icon"],
            unique_fields=["aaguid"],
        )

    self.info("Successfully imported FIDO Alliance MDS blobs and AAGUIDs.")
