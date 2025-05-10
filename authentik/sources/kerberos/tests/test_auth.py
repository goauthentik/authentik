"""Kerberos Source Auth tests"""

from django.contrib.auth.hashers import is_password_usable

from authentik.core.models import User
from authentik.crypto.generators import generate_id
from authentik.sources.kerberos.auth import KerberosBackend
from authentik.sources.kerberos.models import KerberosSource, UserKerberosSourceConnection
from authentik.sources.kerberos.tests.utils import KerberosTestCase


class TestKerberosAuth(KerberosTestCase):
    """Kerberos Auth tests"""

    def setUp(self):
        self.source = KerberosSource.objects.create(
            name="kerberos",
            slug="kerberos",
            realm=self.realm.realm,
            sync_users=False,
            sync_users_password=False,
            password_login_update_internal_password=True,
        )
        self.user = User.objects.create(username=generate_id())
        self.user.set_unusable_password()
        self.user.save()
        UserKerberosSourceConnection.objects.create(
            source=self.source, user=self.user, identifier=self.realm.user_princ
        )

    def test_auth_username(self):
        """Test auth username"""
        backend = KerberosBackend()
        self.assertEqual(
            backend.authenticate(
                None, username=self.user.username, password=self.realm.password("user")
            ),
            self.user,
        )

    def test_auth_principal(self):
        """Test auth principal"""
        backend = KerberosBackend()
        self.assertEqual(
            backend.authenticate(
                None, username=self.realm.user_princ, password=self.realm.password("user")
            ),
            self.user,
        )

    def test_internal_password_update(self):
        """Test internal password update"""
        backend = KerberosBackend()
        backend.authenticate(
            None, username=self.realm.user_princ, password=self.realm.password("user")
        )
        self.user.refresh_from_db()
        self.assertTrue(is_password_usable(self.user.password))
