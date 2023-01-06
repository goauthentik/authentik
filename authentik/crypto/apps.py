"""authentik crypto app config"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.generators import generate_id

if TYPE_CHECKING:
    from authentik.crypto.models import CertificateKeyPair

MANAGED_KEY = "goauthentik.io/crypto/jwt-managed"


class AuthentikCryptoConfig(ManagedAppConfig):
    """authentik crypto app config"""

    name = "authentik.crypto"
    label = "authentik_crypto"
    verbose_name = "authentik Crypto"
    default = True

    def reconcile_load_crypto_tasks(self):
        """Load crypto tasks"""
        self.import_module("authentik.crypto.tasks")

    def _create_update_cert(self, cert: Optional["CertificateKeyPair"] = None):
        from authentik.crypto.builder import CertificateBuilder
        from authentik.crypto.models import CertificateKeyPair

        builder = CertificateBuilder("authentik Internal JWT Certificate")
        builder.build(
            subject_alt_names=["goauthentik.io"],
            validity_days=360,
        )
        if not cert:
            cert = CertificateKeyPair()
        builder.cert = cert
        builder.cert.managed = MANAGED_KEY
        builder.save()

    def reconcile_managed_jwt_cert(self):
        """Ensure managed JWT certificate"""
        from authentik.crypto.models import CertificateKeyPair

        certs = CertificateKeyPair.objects.filter(managed=MANAGED_KEY)
        if not certs.exists():
            self._create_update_cert()
            return
        cert: CertificateKeyPair = certs.first()
        now = datetime.now()
        if now < cert.certificate.not_valid_before or now > cert.certificate.not_valid_after:
            self._create_update_cert(cert)

    def reconcile_self_signed(self):
        """Create self-signed keypair"""
        from authentik.crypto.builder import CertificateBuilder
        from authentik.crypto.models import CertificateKeyPair

        name = "authentik Self-signed Certificate"
        if CertificateKeyPair.objects.filter(name=name).exists():
            return
        builder = CertificateBuilder(name)
        builder.build(subject_alt_names=[f"{generate_id()}.self-signed.goauthentik.io"])
        builder.save()
