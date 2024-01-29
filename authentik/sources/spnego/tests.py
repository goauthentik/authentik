"""SPNEGO Source tests"""
import os
from base64 import b64decode, b64encode
from copy import deepcopy
from pathlib import Path

import gssapi
from django.urls import reverse
from k5test import realm
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.sources.spnego.models import SPNEGOSource


class TestSPNEGOSource(APITestCase):
    """SPNEGO Source tests"""

    @classmethod
    def setUpClass(cls):
        cls.realm = realm.K5Realm()

        cls.realm.http_princ = f"HTTP/testserver@{cls.realm.realm}"
        cls.realm.http_keytab = os.path.join(cls.realm.tmpdir, "http_keytab")
        cls.realm.addprinc(cls.realm.http_princ)
        cls.realm.extract_keytab(cls.realm.http_princ, cls.realm.http_keytab)

        cls._saved_env = deepcopy(os.environ)
        for k, v in cls.realm.env.items():
            os.environ[k] = v

    @classmethod
    def tearDownClass(cls):
        cls.realm.stop()
        del cls.realm

        for k in deepcopy(os.environ):
            if k in cls._saved_env:
                os.environ[k] = cls._saved_env[k]
            else:
                del os.environ[k]
        cls._saved_env = None

    def setUp(self):
        self.source = SPNEGOSource.objects.create(
            name="test",
            slug="test",
            keytab=b64encode(Path(self.realm.http_keytab).read_bytes()).decode(),
        )
        # Force store creation early
        self.source.get_gssapi_store()
        print(b64encode(Path(self.realm.http_keytab).read_bytes()))

    def test_api_read(self):
        """Test reading a source"""
        self.client.force_login(create_test_admin_user())
        response = self.client.get(
            reverse(
                "authentik_api:spnegosource-detail",
                kwargs={
                    "slug": self.source.slug,
                },
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_source_login(self):
        """test login view"""
        response = self.client.get(
            reverse(
                "authentik_sources_spnego:login",
                kwargs={"source_slug": self.source.slug},
            )
        )
        self.assertEqual(response.status_code, 302)

        endpoint = response.headers["Location"]

        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["WWW-Authenticate"], "Negotiate")

        server_name = gssapi.names.Name("HTTP/testserver@")
        client_ctx = gssapi.sec_contexts.SecurityContext(name=server_name, usage="initiate")

        status = 401
        server_token = None
        while status == 401 and not client_ctx.complete:
            client_token = client_ctx.step(server_token)
            if not client_token:
                break
            response = self.client.get(
                endpoint,
                headers={"Authorization": f"Negotiate {b64encode(client_token).decode('ascii')}"},
            )
            status = response.status_code
            if status == 401:
                server_token = b64decode(response.headers["WWW-Authenticate"][9:].strip())

        # 400 because no enroll flow
        self.assertEqual(status, 400)
