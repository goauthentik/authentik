"""Tests for the validate_base_url helper"""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from authentik.tenants.utils import validate_base_url


class TestValidateBaseURL(SimpleTestCase):
    """validate_base_url only requires an http(s) scheme followed by something"""

    def test_validate(self):
        cases = {
            # Empty means the base URL has not been configured, which is allowed.
            "": True,
            "https://authentik.company": True,
            "http://authentik.company": True,
            "HTTPS://authentik.company": True,
            "https://authentik.company/authentik": True,
            # Hostnames Django's URLValidator rejects.
            "https://auth.svr001": True,
            "https://auth": True,
            "https://auth.s1": True,
            "https://my_host.example.com": True,
            "http://localhost:9000": True,
            "https://192.168.1.5:9443": True,
            "https://[fd00::1]:9443": True,
            # Simple mistakes, which are the only thing this rejects.
            "authentik.company": False,
            "//authentik.company": False,
            "not a url": False,
            "ftp://authentik.company": False,
            "javascript:alert(1)": False,
            "https://": False,
            "http://": False,
        }
        for value, valid in cases.items():
            with self.subTest(value=value):
                if valid:
                    validate_base_url(value)
                    continue
                with self.assertRaises(ValidationError):
                    validate_base_url(value)
