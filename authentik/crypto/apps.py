"""authentik crypto app config"""
from datetime import datetime
from importlib import import_module
from typing import TYPE_CHECKING, Optional

from django.apps import AppConfig
from django.db import DatabaseError, ProgrammingError

if TYPE_CHECKING:
    from authentik.crypto.models import CertificateKeyPair

MANAGED_KEY = "goauthentik.io/crypto/jwt-managed"


class AuthentikCryptoConfig(AppConfig):
    """authentik crypto app config"""

    name = "authentik.crypto"
    label = "authentik_crypto"
    verbose_name = "authentik Crypto"

    def ready(self):
        import_module("authentik.crypto.tasks")
        try:
            self.reconcile_managed_jwt_cert()
        except (ProgrammingError, DatabaseError):
            pass

    def _create(self, cert: Optional["CertificateKeyPair"] = None):
        from authentik.crypto.builder import CertificateBuilder
        from authentik.crypto.models import CertificateKeyPair

        builder = CertificateBuilder()
        builder.common_name = "goauthentik.io"
        builder.build(
            subject_alt_names=["goauthentik.io"],
            validity_days=360,
        )
        if not cert:

            cert = CertificateKeyPair()
        cert.certificate_data = builder.certificate
        cert.key_data = builder.private_key
        cert.name = "authentik Internal JWT Certificate"
        cert.managed = MANAGED_KEY
        cert.save()

    def reconcile_managed_jwt_cert(self):
        from authentik.crypto.models import CertificateKeyPair

        certs = CertificateKeyPair.objects.filter(managed=MANAGED_KEY)
        if not certs.exists():
            self._create()
            return
        cert: CertificateKeyPair = certs.first()
        now = datetime.now()
        if now < cert.certificate.not_valid_before or now > cert.certificate.not_valid_after:
            self._create(cert)
