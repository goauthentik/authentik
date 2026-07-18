"""Kerberos Source test utils"""

import os
from copy import deepcopy
from time import sleep

from k5test import realm
from rest_framework.test import APITestCase


class KerberosTestCase(APITestCase):
    """Kerberos Test Case"""

    @classmethod
    def setUpClass(cls):
        cls.realm = realm.K5Realm(start_kadmind=True)

        cls.realm.http_princ = f"HTTP/testserver@{cls.realm.realm}"
        cls.realm.http_keytab = os.path.join(cls.realm.tmpdir, "http_keytab")
        cls.realm.addprinc(cls.realm.http_princ)
        cls.realm.extract_keytab(cls.realm.http_princ, cls.realm.http_keytab)

        cls._saved_env = deepcopy(os.environ)
        for k, v in cls.realm.env.items():
            os.environ[k] = v
        # Wait for everything to start correctly
        # Otherwise leads to flaky tests
        sleep(5)

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
