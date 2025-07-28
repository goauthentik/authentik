"""MDS Helpers"""

from functools import lru_cache
from json import loads
from pathlib import Path

from django.core.cache import cache
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _
from django_dramatiq_postgres.middleware import CurrentTask
from dramatiq.actor import actor
from fido2.mds3 import filter_revoked, parse_blob

from authentik.stages.authenticator_webauthn.models import (
    UNKNOWN_DEVICE_TYPE_AAGUID,
    WebAuthnDeviceType,
)
from authentik.tasks.models import Task

CACHE_KEY_MDS_NO = "goauthentik.io/stages/authenticator_webauthn/mds_no"
AAGUID_BLOB_PATH = Path(__file__).parent / "mds" / "aaguid.json"
MDS_BLOB_PATH = Path(__file__).parent / "mds" / "blob.jwt"
MDS_CA_PATH = Path(__file__).parent / "mds" / "root-r3.crt"


@lru_cache
def mds_ca() -> bytes:
    """Cache MDS Signature CA, GlobalSign Root CA - R3"""
    with open(MDS_CA_PATH, mode="rb") as _raw_root:
        return _raw_root.read()


@actor(description=_("Background task to import FIDO Alliance MDS blob and AAGUIDs into database."))
def webauthn_mds_import(force=False):
    """Background task to import FIDO Alliance MDS blob and AAGUIDs into database"""
    self: Task = CurrentTask.get_task()
    with open(MDS_BLOB_PATH, mode="rb") as _raw_blob:
        blob = parse_blob(_raw_blob.read(), mds_ca())
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
