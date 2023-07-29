"""authentik Kerberos provider tests"""
# pylint: disable=duplicate-code
from django.test import TestCase

from authentik.core.tests.utils import create_test_flow
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm


class TestKerberosKeys(TestCase):
    """Test KerberosKeys"""

    def setUp(self) -> None:
        self.realm: KerberosRealm = KerberosRealm.objects.create(
            name="EXAMPLE.ORG",
        )
        self.provider: KerberosProvider = KerberosProvider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            realm=self.realm,
            service_principal_name="test",
        )

    def test_keytab_kvno_increment(self) -> None:
        """Test provider keytab kvno increment"""
        kvno = self.provider.kerberoskeys.kvno
        self.provider.secret = "test1"
        self.provider.save()
        self.assertLess(kvno, self.provider.kerberoskeys.kvno)

    def test_keytab_kvno_increment_maxvalue(self) -> None:
        """Test provider keytab kvno wrap after max value"""
        self.provider.kerberoskeys.kvno = 2**32 - 1
        self.provider.kerberoskeys.save()
        self.provider.secret = "test2"
        self.provider.save()
        self.assertEqual(self.provider.kerberoskeys.kvno, 1)

    def test_keytab_kvno_increment_mod256(self) -> None:
        """Test provider keytab skip of mod 2**8"""
        self.provider.kerberoskeys.kvno = 2**8 - 1
        self.provider.kerberoskeys.save()
        self.provider.secret = "test3"
        self.provider.save()
        self.assertEqual(self.provider.kerberoskeys.kvno, 2**8 + 1)
