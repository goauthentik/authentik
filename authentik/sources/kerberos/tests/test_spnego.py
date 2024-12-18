"""Kerberos Source SPNEGO tests"""

from base64 import b64decode, b64encode
from pathlib import Path
from sys import platform
from unittest import skipUnless

import gssapi
from django.urls import reverse

from authentik.core.tests.utils import create_test_admin_user
from authentik.sources.kerberos.models import KerberosSource
from authentik.sources.kerberos.tests.utils import KerberosTestCase


class TestSPNEGOSource(KerberosTestCase):
    """Kerberos Source SPNEGO tests"""

    def setUp(self):
        self.source = KerberosSource.objects.create(
            name="test",
            slug="test",
            spnego_keytab=b64encode(Path(self.realm.http_keytab).read_bytes()).decode(),
        )
        # Force store creation early
        self.source.get_gssapi_store()

    def test_api_read(self):
        """Test reading a source"""
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:kerberossource-detail",
                kwargs={
                    "slug": self.source.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)

    @skipUnless(platform.startswith("linux"), "Requires compatible GSSAPI implementation")
    def test_source_login(self):
        """test login view"""
        response = self.client.get(
            reverse(
                "authentik_sources_kerberos:spnego-login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(response.status_code, 302)

        endpoint = response.headers["Location"]

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Negotiate")

        server_name = gssapi.names.Name("HTTP/testserver@")
        client_creds = gssapi.creds.Credentials(
            usage="initiate", store={"ccache": self.realm.ccache}
        )
        client_ctx = gssapi.sec_contexts.SecurityContext(
            name=server_name, usage="initiate", creds=client_creds
        )

        status = 401
        server_token = None
        while status == 401 and not client_ctx.complete:  # noqa: PLR2004
            client_token = client_ctx.step(server_token)
            if not client_token:
                break
            response = self.client.get(
                endpoint,
                headers={"Authorization": f"Negotiate {b64encode(client_token).decode('ascii')}"},
            )
            status = response.status_code
            if status == 401:  # noqa: PLR2004
                server_token = b64decode(response.headers["WWW-Authenticate"][9:].strip())

        # 400 because no enroll flow
        self.assertEqual(status, 400)
