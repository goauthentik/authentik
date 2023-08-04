"""KerberosProvider keytab tests"""
# pylint: disable=duplicate-code
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.providers.kerberos.lib import crypto


class TestKerberosProviderCrypto(APITestCase):
    def test_checksum_hmac_sha384_192_aes256(self) -> None:
        tests = (
            {
                "data": b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F\x10\x11\x12\x13\x14",
                "usage": 2,
                "key": b"\x6D\x40\x4D\x37\xFA\xF7\x9F\x9D\xF0\xD3\x35\x68\xD3\x20\x66\x98\x00\xEB\x48\x36\x47\x2E\xA8\xA0\x26\xD1\x6B\x71\x82\x46\x0C\x52",
                "checksum": b"\x45\xEE\x79\x15\x67\xEE\xFC\xA3\x7F\x4A\xC1\xE0\x22\x2D\xE8\x0D\x43\xC3\xBF\xA0\x66\x99\x67\x2A",
            },
        )

        for test in tests:
            checksum = crypto.Aes256CtsHmacSha384192.checksum_hash(
                key=test["key"],
                data=test["data"],
                usage=test["usage"],
            )
            self.assertTrue(
                crypto.Aes256CtsHmacSha384192.verify_checksum(
                    key=test["key"],
                    data=test["data"],
                    usage=test["usage"],
                    checksum=test["checksum"],
                )
            )
            self.assertEqual(checksum, test["checksum"])
