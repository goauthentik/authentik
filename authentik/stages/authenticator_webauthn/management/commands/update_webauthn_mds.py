from django.core.management.base import BaseCommand
from fido2.mds3 import parse_blob
from structlog.stdlib import get_logger

from authentik.common.utils.http import get_http_session
from authentik.stages.authenticator_webauthn.tasks import AAGUID_BLOB_PATH, MDS_BLOB_PATH, mds_ca

MDS3_URL = "https://mds3.fidoalliance.org/"
AAGUID_URL = "https://passkeydeveloper.github.io/passkey-authenticator-aaguids/aaguid.json"


class Command(BaseCommand):
    """Update FIDO Alliances' MDS3 blob and validate it."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger()

    def update_fido_mds(self):
        with open(MDS_BLOB_PATH, "w", encoding="utf-8") as _raw_file:
            _raw_file.write(get_http_session().get(MDS3_URL).text)
        self.logger.info("Updated MDS blob")
        with open(MDS_BLOB_PATH, mode="rb") as _raw_blob:
            parse_blob(_raw_blob.read(), mds_ca())
        self.logger.info("Successfully validated MDS blob")

    def update_passkey_aaguids(self):
        with open(AAGUID_BLOB_PATH, "w", encoding="utf-8") as _raw_file:
            _raw_file.write(get_http_session().get(AAGUID_URL).text)
        self.logger.info("Updated AAGUID blob")

    def handle(self, *args, **options):
        self.update_fido_mds()
        self.update_passkey_aaguids()
