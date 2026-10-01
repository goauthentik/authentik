"""Kerberos kadm5 client library tests"""

from django.test import TestCase
from kadmin import exceptions as kadmin_exceptions

from authentik.lib.generators import generate_id
from authentik.sources.kerberos.models import KAdminType, KerberosSource, Krb5ConfContext


class TestKAdm5Libraries(TestCase):
    """python-kadmin-rs loads the kadm5 client library only when it connects, so a missing library
    shows up nowhere else. The sync tests load the MIT one against the test KDC. A failed MIT
    connection unloads the library but leaves its error table registered, and the next Kerberos
    error message crashes the process, so only the Heimdal one is tried here"""

    def test_heimdal_library_loads(self):
        """Without a KDC connecting fails, but not because the library is missing"""
        realm = generate_id().upper()
        source = KerberosSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            realm=realm,
            krb5_conf=(
                "[libdefaults]\n"
                f"    default_realm = {realm}\n"
                "    dns_lookup_kdc = false\n"
                "    dns_lookup_realm = false\n"
            ),
            kadmin_type=KAdminType.HEIMDAL,
            sync_users=True,
            sync_principal=f"sync@{realm}",
            sync_password=generate_id(),
        )
        with (
            Krb5ConfContext(source),
            self.assertRaises(kadmin_exceptions.PyKAdminException) as ctx,
        ):
            source.connection()
        self.assertNotIsInstance(ctx.exception, kadmin_exceptions.LibraryLoadError)
