"""Tests for the base_url field validators"""

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from authentik.tenants.models import Tenant


class TestValidateBaseURL(SimpleTestCase):
    """base_url accepts an http or https URL whose host needs no domain part"""

    def test_validate(self):
        field = Tenant._meta.get_field("base_url")
        cases = {
            "https://authentik.company": True,
            "http://authentik.company": True,
            "HTTPS://authentik.company": True,
            "https://authentik.company/authentik": True,
            # Hostnames Django's own URLValidator rejects
            "https://auth.svr001": True,
            "https://auth": True,
            "https://auth.s1": True,
            "http://localhost:9000": True,
            "https://192.168.1.5:9443": True,
            "https://[fd00::1]:9443": True,
            # Not a URL at all.
            "authentik.company": False,
            "//authentik.company": False,
            "not a url": False,
            "https://": False,
            "http://": False,
            # Only http and https.
            "ftp://authentik.company": False,
            "javascript:alert(1)": False,
            # A host that is not a host.
            "http:///nohost": False,
            "https://.": False,
            "https://auth svr001": False,
            "https://my_host.example.com": False,
            "https://auth.svr001\nBcc: someone@example.com": False,
            "https://auth.svr001\tfoo": False,
        }
        for value, valid in cases.items():
            with self.subTest(value=value):
                if valid:
                    field.run_validators(value)
                    continue
                with self.assertRaises(ValidationError):
                    field.run_validators(value)
