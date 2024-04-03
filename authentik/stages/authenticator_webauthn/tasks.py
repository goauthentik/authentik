"""MDS Helpers"""

from functools import lru_cache
from pathlib import Path

from django.core.cache import cache
from django.db.transaction import atomic
from fido2.mds3 import filter_revoked, parse_blob

from authentik.root.celery import CELERY_APP
from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    WebAuthnDeviceType,
)

CACHE_KEY_MDS_NO = "goauthentik.io/stages/authenticator_webauthn/mds_no"
MDS_BLOB_PATH = Path(__file__).parent / "mds" / "blob.jwt"
MDS_CA_PATH = Path(__file__).parent / "mds" / "root-r3.crt"


@lru_cache
def mds_ca() -> bytes:
    """Cache MDS Signature CA, GlobalSign Root CA - R3"""
    with open(MDS_CA_PATH, mode="rb") as _raw_root:
        return _raw_root.read()


@CELERY_APP.task()
def webauthn_mds_import(force=False):
    """Background task to import FIDO Alliance MDS blob into database"""
    with open(MDS_BLOB_PATH, mode="rb") as _raw_blob:
        blob = parse_blob(_raw_blob.read(), mds_ca())
    with atomic():
        WebAuthnDeviceType.objects.update_or_create(
            aaguid=UNKNOWN_DEVICE_TYPE_AAGUID,
            defaults={
                "description": "authentik: Unknown devices",
            },
        )
        if cache.get(CACHE_KEY_MDS_NO) == blob.no and not force:
            return
        for entry in blob.entries:
            aaguid = entry.aaguid
            if not aaguid:
                continue
            if not filter_revoked(entry):
                WebAuthnDeviceType.objects.filter(aaguid=str(aaguid)).delete()
                continue
            metadata = entry.metadata_statement
            WebAuthnDeviceType.objects.update_or_create(
                aaguid=str(aaguid),
                defaults={"description": metadata.description, "icon": metadata.icon},
            )
    cache.set(CACHE_KEY_MDS_NO, blob.no)
