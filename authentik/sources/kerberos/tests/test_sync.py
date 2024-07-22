"""Kerberos Source sync tests"""

from authentik.core.models import User
from authentik.events.models import Event, EventAction
from authentik.lib.generators import generate_id
from authentik.sources.kerberos.models import KerberosPropertyMapping, KerberosSource
from authentik.sources.kerberos.sync import KerberosSync
from authentik.sources.kerberos.tasks import kerberos_sync_all
from authentik.sources.kerberos.tests.utils import KerberosTestCase


class TestKerberosSync(KerberosTestCase):
    """Kerberos Sync tests"""

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

    def test_sync_mapping(self):
        """Test property mappings"""
        noop = KerberosPropertyMapping.objects.create(name=generate_id(), expression="return {}")
        email = KerberosPropertyMapping.objects.create(
            name=generate_id(), expression='return {"email": principal.lower()}'
        )
        dont_sync_service = KerberosPropertyMapping.objects.create(
            name=generate_id(),
            expression='if "/" in principal:\n    return {"username": None}\nreturn {}',
        )
        self.source.property_mappings.set([noop, email, dont_sync_service])

        KerberosSync(self.source).sync()

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
        kerberos_sync_all.delay().get()
