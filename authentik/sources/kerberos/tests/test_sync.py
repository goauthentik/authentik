"""Kerberos Source sync tests"""

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.sources.kerberos.models import KerberosSource, KerberosSourcePropertyMapping
from authentik.sources.kerberos.sync import KerberosSync
from authentik.sources.kerberos.tasks import kerberos_sync
from authentik.sources.kerberos.tests.utils import KerberosTestCase
from authentik.tasks.models import Task


class TestKerberosSync(KerberosTestCase):
    """Kerberos Sync tests"""

    @apply_blueprint("system/sources-kerberos.yaml")
    def setUp(self):
        self.source: KerberosSource = KerberosSource.objects.create(
            name="kerberos",
            slug="kerberos",
            realm=self.realm.realm,
            sync_users=True,
            sync_users_password=True,
            sync_principal=self.realm.admin_princ,
            sync_password=self.realm.password("admin"),
        )
        self.source.user_property_mappings.set(
            KerberosSourcePropertyMapping.objects.filter(
                managed__startswith="goauthentik.io/sources/kerberos/user/default/"
            )
        )

    def test_default_mappings(self):
        """Test default mappings"""
        KerberosSync(self.source, Task()).sync()

        self.assertTrue(
            User.objects.filter(username=self.realm.user_princ.rsplit("@", 1)[0]).exists()
        )
        self.assertFalse(
            User.objects.filter(username=self.realm.nfs_princ.rsplit("@", 1)[0]).exists()
        )

    def test_sync_mapping(self):
        """Test property mappings"""
        noop = KerberosSourcePropertyMapping.objects.create(
            name=generate_id(), expression="return {}"
        )
        email = KerberosSourcePropertyMapping.objects.create(
            name=generate_id(), expression='return {"email": principal.lower()}'
        )
        dont_sync_service = KerberosSourcePropertyMapping.objects.create(
            name=generate_id(),
            expression='if "/" in principal:\n    return {"username": None}\nreturn {}',
        )
        self.source.user_property_mappings.set([noop, email, dont_sync_service])

        KerberosSync(self.source, Task()).sync()

        self.assertTrue(
            User.objects.filter(username=self.realm.user_princ.rsplit("@", 1)[0]).exists()
        )
        self.assertEqual(
            User.objects.get(username=self.realm.user_princ.rsplit("@", 1)[0]).email,
            self.realm.user_princ.lower(),
        )
        self.assertFalse(
            User.objects.filter(username=self.realm.nfs_princ.rsplit("@", 1)[0]).exists()
        )

    def test_tasks(self):
        """Test Scheduled tasks"""
        kerberos_sync.send(self.source.pk)
        self.assertTrue(
            User.objects.filter(username=self.realm.user_princ.rsplit("@", 1)[0]).exists()
        )
