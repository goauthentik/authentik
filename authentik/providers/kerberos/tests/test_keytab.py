"""KerberosProvider keytab tests"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.kerberos.keytab import Keytab
from authentik.lib.kerberos.principal import PrincipalName
from authentik.providers.kerberos.models import KerberosProvider, KerberosRealm


class TestKerberosProviderKeytab(APITestCase):
    """Test KerberosProvider keytab route"""

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
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_keytab(self) -> None:
        """Test provider keytab retrieval"""
        response = self.client.get(
            reverse("authentik_api:kerberosprovider-keytab", kwargs={"pk":
                                                                     self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("Content-Type"),
            "application/octet-stream",
        )
        keytab = Keytab.from_bytes(response.content)
        self.assertEqual(
            set(e.key.key_type for e in keytab.entries),
            set(self.provider.keys.keys()),
        )
        for entry in keytab.entries:
            self.assertEqual(
                entry.principal.name.name,
                PrincipalName.from_spn(self.provider.service_principal_name).name,
            )
            self.assertEqual(
                entry.principal.name.name_type,
                PrincipalName.from_spn(self.provider.service_principal_name).name_type,
            )
            self.assertEqual(
                entry.principal.realm,
                self.realm.name,
            )
            self.assertEqual(
                entry.kvno,
                self.provider.kvno,
            )
            self.assertEqual(
                entry.kvno8,
                self.provider.kvno % 2**8,
            )
            self.assertEqual(
                entry.key.key,
                self.provider.keys[entry.key.key_type],
            )


    def test_keytab_kvno_mod256(self) -> None:
        """Test provider keytab retrieval"""
        self.provider.kvno = 2**8 + 1
        self.provider.save()
        response = self.client.get(
            reverse("authentik_api:kerberosprovider-keytab", kwargs={"pk":
                                                                     self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        keytab = Keytab.from_bytes(response.content)
        for entry in keytab.entries:
            self.assertEqual(
                entry.kvno,
                self.provider.kvno,
            )
            self.assertEqual(
                entry.kvno8,
                self.provider.kvno % 2**8,
            )
