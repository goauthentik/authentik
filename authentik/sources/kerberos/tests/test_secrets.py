"""Kerberos credential files and cached connections follow secret changes."""

from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import PropertyMock, patch

from django.test import TestCase

from authentik.lib.generators import generate_id
from authentik.secrets.models import Secret, SecretType
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
            ("sync_keytab_secret", "with_keytab"),
            ("sync_ccache_secret", "with_ccache"),
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
        self.source.spnego_keytab_secret = secret
        self.source.spnego_ccache_secret = secret
        store = self.source.get_gssapi_store()
        for value in store.values():
            self.assertEqual(Path(value.removeprefix("FILE:")).read_bytes(), b"credential file")

    def test_credential_replacement_refreshes_connection(self):
        self.source.secret = Secret.objects.create(name=generate_id(), value="old password")
        self.source.save()
        with patch("authentik.sources.kerberos.models.KAdmin.with_password") as factory:
            first = self.source.connection()
            self.assertIs(self.source.connection(), first)
            factory.assert_called_once()
            self.source.secret.replace_value("new password")
            self.source.refresh_from_db()
            self.source.connection()
            self.assertEqual(factory.call_count, 2)
            self.assertEqual(factory.call_args.args[2], "new password")
