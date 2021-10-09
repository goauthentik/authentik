"""Crypto managed objects"""
from datetime import datetime
from typing import Optional

from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.models import CertificateKeyPair
from authentik.managed.manager import ObjectManager

MANAGED_KEY = "goauthentik.io/crypto/jwt-managed"


class CryptoManager(ObjectManager):
    """Crypto managed objects"""

    def _create(self, cert: Optional[CertificateKeyPair] = None):
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

    def reconcile(self):
        certs = CertificateKeyPair.objects.filter(managed=MANAGED_KEY)
        if not certs.exists():
            self._create()
            return []
        cert: CertificateKeyPair = certs.first()
        now = datetime.now()
        if now < cert.certificate.not_valid_before or now > cert.certificate.not_valid_after:
            self._create(cert)
            return []
        return []
