"""Kerberos Principal tests"""
from django.test import TestCase

from authentik.lib.kerberos.protocol import PrincipalName, PrincipalNameType


class TestPrincipal(TestCase):
    """Kerberos Principal tests"""

    def test_from_spn_valid(self):
        """Test Principal creation from a valid service principal name"""
        data = (
            (
                "test@EXAMPLE.ORG",
                PrincipalName.from_components(
                    name_type=PrincipalNameType.NT_SRV_INST, name=["test"],
                ),
            ),
            (
                "host/test.example.org@EXAMPLE.ORG",
                PrincipalName.from_components(
                    name_type=PrincipalNameType.NT_SRV_HST,
                    name=["host", "test.example.org"],
                ),
            ),
            (
                "test1/test2/test.example.org@EXAMPLE.ORG",
                PrincipalName.from_components(
                    name_type=PrincipalNameType.NT_SRV_XHST,
                    name=["test1", "test2", "test.example.org"],
                ),
            ),
            (
                "test",
                PrincipalName.from_components(name_type=PrincipalNameType.NT_SRV_INST, name=["test"]),
            ),
            (
                "host/test.example.org",
                PrincipalName.from_components(
                    name_type=PrincipalNameType.NT_SRV_HST,
                    name=["host", "test.example.org"],
                ),
            ),
            (
                "test1/test2/test.example.org",
                PrincipalName.from_components(
                    name_type=PrincipalNameType.NT_SRV_XHST,
                    name=["test1", "test2", "test.example.org"],
                ),
            ),
        )
        for spn, expected in data:
            result = PrincipalName.from_spn(spn)
            self.assertEqual(result["name-type"], expected["name-type"])
            self.assertEqual(result["name-string"], expected["name-string"])

    def test_from_spn_invalid(self):
        """Test Principal creation from an invalid service principal name"""
        with self.assertRaises(ValueError):
            PrincipalName.from_spn("")
        with self.assertRaises(ValueError):
            PrincipalName.from_spn("/")
        with self.assertRaises(ValueError):
            PrincipalName.from_spn("@")
        with self.assertRaises(ValueError):
            PrincipalName.from_spn("/@")
        with self.assertRaises(ValueError):
            PrincipalName.from_spn("@EXAMPLE.ORG")
        with self.assertRaises(ValueError):
            PrincipalName.from_spn("test@")
