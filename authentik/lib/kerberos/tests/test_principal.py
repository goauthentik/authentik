from datetime import datetime

from django.test import TestCase

from authentik.lib.kerberos.exceptions import KerberosException
from authentik.lib.kerberos.principal import PrincipalName, PrincipalNameType


class TestPrincipal(TestCase):
    def test_from_spn_valid(self):
        data = (
            (
                "test@EXAMPLE.ORG",
                PrincipalName(
                    name_type=PrincipalNameType.NT_SRV_INST, name=["test"], realm="EXAMPLE.ORG"
                ),
            ),
            (
                "host/test.example.org@EXAMPLE.ORG",
                PrincipalName(
                    name_type=PrincipalNameType.NT_SRV_HST,
                    name=["host", "test.example.org"],
                    realm="EXAMPLE.ORG",
                ),
            ),
            (
                "test1/test2/test.example.org@EXAMPLE.ORG",
                PrincipalName(
                    name_type=PrincipalNameType.NT_SRV_XHST,
                    name=["test1", "test2", "test.example.org"],
                    realm="EXAMPLE.ORG",
                ),
            ),
            (
                "test",
                PrincipalName(name_type=PrincipalNameType.NT_SRV_INST, name=["test"], realm=None),
            ),
            (
                "host/test.example.org",
                PrincipalName(
                    name_type=PrincipalNameType.NT_SRV_HST,
                    name=["host", "test.example.org"],
                    realm=None,
                ),
            ),
            (
                "test1/test2/test.example.org",
                PrincipalName(
                    name_type=PrincipalNameType.NT_SRV_XHST,
                    name=["test1", "test2", "test.example.org"],
                    realm=None,
                ),
            ),
        )
        for spn, expected in data:
            result = PrincipalName.from_spn(spn)
            self.assertEqual(result.name_type, expected.name_type)
            self.assertEqual(result.name, expected.name)
            self.assertEqual(result.realm, expected.realm)

    def test_from_spn_invalid(self):
        with self.assertRaises(KerberosException):
            PrincipalName.from_spn("")
        with self.assertRaises(KerberosException):
            PrincipalName.from_spn("/")
        with self.assertRaises(KerberosException):
            PrincipalName.from_spn("@")
        with self.assertRaises(KerberosException):
            PrincipalName.from_spn("/@")
        with self.assertRaises(KerberosException):
            PrincipalName.from_spn("@EXAMPLE.ORG")
        with self.assertRaises(KerberosException):
            PrincipalName.from_spn("test@")
