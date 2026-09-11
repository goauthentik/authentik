"""Test LDAP source SASL EXTERNAL authentication."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID, ObjectIdentifier
from django.db.models import Q
from docker.types import Healthcheck

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.sources.ldap.auth import LDAPBackend
from authentik.sources.ldap.models import (
    LDAPSource,
    LDAPSourceBindMethod,
    LDAPSourcePropertyMapping,
)
from authentik.sources.ldap.password import LDAPPasswordChanger
from authentik.sources.ldap.sync.users import UserLDAPSynchronizer
from authentik.tasks.models import Task
from tests.live import E2ETestCase

OPENLDAP_IMAGE = (
    "docker.io/osixia/openldap:2.6.10-alpha@"
    "sha256:80a577d7d4471c4db662195111e5709665b6fcbd6679094d05402b8c620e2607"
)
LDAP_PASSWORD = "correct-horse-battery-staple"
NEW_LDAP_PASSWORD = "correct-staple-horse-battery"


def build_certificate(
    common_name: str,
    issuer: x509.Certificate | None = None,
    issuer_key: rsa.RSAPrivateKey | None = None,
    extended_key_usage: ObjectIdentifier | None = None,
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Build a CA or CA-signed certificate for the LDAP fixture."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    is_ca = issuer is None
    now = datetime.now(UTC)
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer.subject if issuer else subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key((issuer_key or key).public_key()),
            critical=False,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=not is_ca,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=is_ca,
                crl_sign=is_ca,
                encipher_only=None,
                decipher_only=None,
            ),
            critical=True,
        )
    )
    if common_name == "localhost":
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False
        )
    if extended_key_usage:
        builder = builder.add_extension(x509.ExtendedKeyUsage([extended_key_usage]), critical=False)
    certificate = builder.sign(issuer_key or key, hashes.SHA256())
    return key, certificate


def private_key_pem(key: rsa.RSAPrivateKey) -> bytes:
    """Serialize a private key for OpenLDAP and authentik."""
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def certificate_pem(certificate: x509.Certificate) -> bytes:
    """Serialize a certificate for OpenLDAP and authentik."""
    return certificate.public_bytes(serialization.Encoding.PEM)


class TestSourceLDAPSASLExternal(E2ETestCase):
    """Test LDAP synchronization with a certificate-authenticated service bind."""

    def setUp(self):
        super().setUp()
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.certificates_dir = Path(self.temp_dir.name)
        self.certificates_dir.chmod(0o755)

        ca_key, ca_certificate = build_certificate("authentik LDAP test CA")
        server_key, server_certificate = build_certificate(
            "localhost", ca_certificate, ca_key, ExtendedKeyUsageOID.SERVER_AUTH
        )
        client_key, client_certificate = build_certificate(
            "authentik LDAP sync", ca_certificate, ca_key, ExtendedKeyUsageOID.CLIENT_AUTH
        )

        certificate_files = {
            "ca.crt": certificate_pem(ca_certificate),
            "tls.crt": certificate_pem(server_certificate),
            "tls.key": private_key_pem(server_key),
            "client.crt": certificate_pem(client_certificate),
            "client.key": private_key_pem(client_key),
        }
        for name, data in certificate_files.items():
            path = self.certificates_dir / name
            path.write_bytes(data)
            path.chmod(0o644)

        self.ca_keypair = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=certificate_files["ca.crt"].decode(),
        )
        self.client_keypair = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=certificate_files["client.crt"].decode(),
            key_data=certificate_files["client.key"].decode(),
        )

        fixtures = Path(__file__).parent / "fixtures" / "openldap-sasl"
        self.openldap = self.run_container(
            image=OPENLDAP_IMAGE,
            hostname="localhost",
            ports={"3890/tcp": None},
            healthcheck=Healthcheck(
                test=[
                    "CMD",
                    "ldapsearch",
                    "-x",
                    "-H",
                    "ldap://localhost:3890",
                    "-b",
                    "",
                    "-s",
                    "base",
                ],
                interval=1_000_000_000,
                timeout=5_000_000_000,
                retries=5,
                start_period=1_000_000_000,
            ),
            environment={
                "OPENLDAP_BOOTSTRAP_ORGANIZATION": "goauthentik.io",
                "OPENLDAP_BOOTSTRAP_SUFFIX": "dc=goauthentik,dc=io",
                "OPENLDAP_BOOTSTRAP_TLS": "true",
                "OPENLDAP_BOOTSTRAP_TLS_VERIFY_CLIENT": "try",
                "OPENLDAP_BOOTSTRAP_TLS_PROTOCOL_MIN": "3.3",
                "OPENLDAP_BOOTSTRAP_TLS_CERT": (
                    "/container/services/openldap/assets/certs/tls.crt"
                ),
                "OPENLDAP_BOOTSTRAP_TLS_CERT_KEY": (
                    "/container/services/openldap/assets/certs/tls.key"
                ),
                "OPENLDAP_BOOTSTRAP_TLS_CA_CERT": (
                    "/container/services/openldap/assets/certs/ca.crt"
                ),
            },
            volumes={
                str(self.certificates_dir): {
                    "bind": "/container/services/openldap/assets/certs",
                    "mode": "ro",
                },
                str(fixtures / "10-users.ldif"): {
                    "bind": (
                        "/container/services/openldap-bootstrap/assets/ldif/data/"
                        "custom/10-users.ldif"
                    ),
                    "mode": "ro",
                },
                str(fixtures / "68-certificate-reader.ldif"): {
                    "bind": (
                        "/container/services/openldap-bootstrap/assets/ldif/config/"
                        "base/68-certificate-reader.ldif"
                    ),
                    "mode": "ro",
                },
            },
        )
        self.ldap_port = self.openldap.ports["3890/tcp"][0]["HostPort"]

    @apply_blueprint("system/sources-ldap.yaml")
    def test_sync_and_user_authentication(self):
        """SASL EXTERNAL syncs users without replacing their password bind."""
        source = LDAPSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            server_uri=f"ldap://localhost:{self.ldap_port}",
            peer_certificate=self.ca_keypair,
            client_certificate=self.client_keypair,
            bind_cn="ignored",
            bind_password="ignored",
            service_bind_method=LDAPSourceBindMethod.SASL_EXTERNAL,
            start_tls=True,
            sni=True,
            base_dn="dc=goauthentik,dc=io",
            additional_user_dn="ou=users",
            object_uniqueness_field="uid",
        )
        source.user_property_mappings.set(
            LDAPSourcePropertyMapping.objects.filter(
                Q(managed__startswith="goauthentik.io/sources/ldap/default-")
                | Q(managed__startswith="goauthentik.io/sources/ldap/openldap-")
            )
        )

        connection = source.connection()
        self.assertEqual(connection.extend.standard.who_am_i(), "dn:cn=authentik ldap sync")
        connection.unbind()

        UserLDAPSynchronizer(source, Task()).sync_full()
        user = User.objects.get(username="alice")
        self.assertEqual(user.email, "alice@example.test")

        backend = LDAPBackend()
        self.assertEqual(backend.auth_user(None, source, LDAP_PASSWORD, username="alice"), user)
        self.assertIsNone(backend.auth_user(None, source, "wrong-password", username="alice"))

        LDAPPasswordChanger(source).change_password(user, NEW_LDAP_PASSWORD)
        self.assertIsNone(backend.auth_user(None, source, LDAP_PASSWORD, username="alice"))
        self.assertEqual(backend.auth_user(None, source, NEW_LDAP_PASSWORD, username="alice"), user)
