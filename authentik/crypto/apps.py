"""authentik crypto app config"""

from datetime import datetime, timezone
from typing import Optional

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.generators import generate_id

MANAGED_KEY = "goauthentik.io/crypto/jwt-managed"


class AuthentikCryptoConfig(ManagedAppConfig):
    """authentik crypto app config"""

    name = "authentik.crypto"
    label = "authentik_crypto"
    verbose_name = "authentik Crypto"
    default = True

    def _create_update_cert(self):
        from authentik.crypto.builder import CertificateBuilder
        from authentik.crypto.models import CertificateKeyPair

        common_name = "authentik Internal JWT Certificate"
        builder = CertificateBuilder(common_name)
        builder.build(
            subject_alt_names=["goauthentik.io"],
            validity_days=360,
        )
        CertificateKeyPair.objects.update_or_create(
            managed=MANAGED_KEY,
            defaults={
                "name": common_name,
                "certificate_data": builder.certificate,
                "key_data": builder.private_key,
            },
        )

    def reconcile_tenant_managed_jwt_cert(self):
        """Ensure managed JWT certificate"""
        from authentik.crypto.models import CertificateKeyPair

        cert: Optional[CertificateKeyPair] = CertificateKeyPair.objects.filter(
            managed=MANAGED_KEY
        ).first()
        now = datetime.now(tz=timezone.utc)
        if not cert or (
            now < cert.certificate.not_valid_after_utc or now > cert.certificate.not_valid_after_utc
        ):
            self._create_update_cert()

    def reconcile_tenant_self_signed(self):
        """Create self-signed keypair"""
        from authentik.crypto.builder import CertificateBuilder
        from authentik.crypto.models import CertificateKeyPair

        name = "authentik Self-signed Certificate"
        if CertificateKeyPair.objects.filter(name=name).exists():
            return
        builder = CertificateBuilder(name)
        builder.build(subject_alt_names=[f"{generate_id()}.self-signed.goauthentik.io"])
        CertificateKeyPair.objects.get_or_create(
            name=name,
            defaults={
                "certificate_data": builder.certificate,
                "key_data": builder.private_key,
            },
        )
