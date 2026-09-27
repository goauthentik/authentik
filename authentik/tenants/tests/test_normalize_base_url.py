"""Tests for the normalize_base_url helper"""

from django.test import SimpleTestCase

from authentik.tenants.utils import normalize_base_url


class TestNormalizeBaseURL(SimpleTestCase):
    """normalize_base_url strips whitespace and trailing slashes"""

    def test_normalize(self):
        cases = {
            None: "",
            "": "",
            "   ": "",
            "https://authentik.company": "https://authentik.company",
            "https://authentik.company/": "https://authentik.company",
            "https://authentik.company///": "https://authentik.company",
            "  https://authentik.company/  ": "https://authentik.company",
            "https://authentik.company/authentik/": "https://authentik.company/authentik",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(normalize_base_url(value), expected)
