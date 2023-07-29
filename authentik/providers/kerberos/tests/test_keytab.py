"""KerberosProvider keytab tests"""
# pylint: disable=duplicate-code
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.providers.kerberos.lib.crypto import get_enctype_from_value
from authentik.providers.kerberos.lib.keytab import Keytab
from authentik.providers.kerberos.lib.protocol import PrincipalName
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm


class TestKerberosProviderKeytab(APITestCase):
    """Test KerberosProvider keytab route"""

    def setUp(self) -> None:
        self.realm: KerberosRealm = KerberosRealm.objects.create(name="EXAMPLE.ORG")
        self.provider: KerberosProvider = KerberosProvider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            spn="test",
        )
        self.provider.realms.add(self.realm)
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_keytab(self) -> None:
        """Test provider keytab retrieval"""
        response = self.client.get(
            reverse("authentik_api:kerberosprovider-keytab", kwargs={"pk": self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Content-Type"),
            "application/octet-stream",
        )
        keytab = Keytab.from_bytes(response.content)
        self.assertEqual(
            set(e.key.key_type for e in keytab.entries),
            set(enctype.ENC_TYPE for enctype in self.provider.kerberoskeys.keys.keys()),
        )
        for entry in keytab.entries:
            self.assertEqual(
                entry.principal.name["name-string"],
                self.provider.principal_name["name-string"],
            )
            self.assertEqual(
                entry.principal.name["name-type"],
                self.provider.principal_name["name-type"],
            )
            self.assertEqual(
                entry.principal.realm,
                self.realm.realm_name,
            )
            self.assertEqual(
                entry.kvno,
                self.provider.kerberoskeys.kvno,
            )
            self.assertEqual(
                entry.kvno8,
                self.provider.kerberoskeys.kvno % 2**8,
            )
            self.assertEqual(
                entry.key.key,
                self.provider.kerberoskeys.keys[get_enctype_from_value(entry.key.key_type.value)],
            )

    def test_keytab_kvno_mod256(self) -> None:
        """Test provider keytab retrieval"""
        self.provider.kerberoskeys.kvno = 2**8 + 1
        self.provider.kerberoskeys.save()
        response = self.client.get(
            reverse("authentik_api:kerberosprovider-keytab", kwargs={"pk": self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        keytab = Keytab.from_bytes(response.content)
        for entry in keytab.entries:
            self.assertEqual(
                entry.kvno,
                self.provider.kerberoskeys.kvno,
            )
            self.assertEqual(
                entry.kvno8,
                self.provider.kerberoskeys.kvno % 2**8,
            )
