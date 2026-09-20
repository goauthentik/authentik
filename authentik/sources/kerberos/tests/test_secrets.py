"""Kerberos credential files and cached connections follow secret changes."""

from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock, patch

from django.test import TestCase

from authentik.crypto.secrets.models import Secret, SecretType
from authentik.lib.generators import generate_id
from authentik.sources.kerberos.api.source import KerberosSourceSerializer
from authentik.sources.kerberos.models import KerberosSource, _kadmin_connections


class TestKerberosSecrets(TestCase):
    def setUp(self):
        self.source = KerberosSource.objects.create(
            name=generate_id(), slug=generate_id(), sync_principal="admin"
        )
        self.addCleanup(_kadmin_connections.pop, str(self.source.pk), None)
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        temporary_path = patch.object(
            KerberosSource,
            "tempdir",
            new_callable=PropertyMock,
            return_value=Path(self.directory.name),
        )
        temporary_path.start()
        self.addCleanup(temporary_path.stop)

    def test_keytab_and_cache_files(self):
        for field, method in [
            ("sync_keytab_ref", "with_keytab"),
            ("sync_ccache_ref", "with_ccache"),
        ]:
            with self.subTest(field=field):
                secret = Secret(type=SecretType.FILE, value=b64encode(b"credential file").decode())
                setattr(self.source, field, secret)
                with patch(f"authentik.sources.kerberos.models.KAdmin.{method}") as factory:
                    self.source._kadmin_init()
                path = Path(factory.call_args.args[2].removeprefix("FILE:"))
                self.assertEqual(path.read_bytes(), b"credential file")
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                setattr(self.source, field, None)
        self.source.spnego_keytab_ref = secret
        self.source.spnego_ccache_ref = secret
        store = self.source.get_gssapi_store()
        for value in store.values():
            self.assertEqual(Path(value.removeprefix("FILE:")).read_bytes(), b"credential file")

    def test_credential_replacement_refreshes_connection(self):
        self.source.sync_password_ref = Secret.objects.create(
            name=generate_id(), value="old password"
        )
        self.source.save()
        with patch("authentik.sources.kerberos.models.KAdmin.with_password") as factory:
            first = self.source.connection()
            self.assertIs(self.source.connection(), first)
            factory.assert_called_once()
            self.source.sync_password_ref.replace_value("new password")
            self.source.refresh_from_db()
            self.source.connection()
            self.assertEqual(factory.call_count, 2)
            self.assertEqual(factory.call_args.args[2], "new password")

    def test_reference_types(self):
        for field in (
            "sync_password_ref",
            "sync_keytab_ref",
            "sync_ccache_ref",
            "spnego_keytab_ref",
            "spnego_ccache_ref",
        ):
            allowed_types = (
                (SecretType.TEXT,)
                if field == "sync_password_ref"
                else (SecretType.MULTILINE, SecretType.FILE)
            )
            for secret_type in SecretType:
                with self.subTest(field=field, type=secret_type):
                    secret = Secret.objects.create(
                        name=generate_id(), type=secret_type, value="aGk="
                    )
                    serializer = KerberosSourceSerializer(
                        instance=self.source, data={field: str(secret.pk)}, partial=True
                    )
                    valid = secret_type in allowed_types
                    self.assertEqual(serializer.is_valid(), valid, serializer.errors)
                    if valid:
                        serializer.save()
                        self.source.refresh_from_db()
                        self.assertEqual(getattr(self.source, field), secret)
                    else:
                        self.assertIn(field, serializer.errors)
