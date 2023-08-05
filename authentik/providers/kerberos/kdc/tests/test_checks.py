"""KerberosProvider KDC checks tests"""
from django.test import TestCase

from authentik.providers.kerberos.kdc.checks import CnameFromKdcReqCheck, PvnoCheck
from authentik.providers.kerberos.kdc.kdcreqhandler import KdcReqMessageHandler


class TestPvnoCheck(TestCase):
    def test_valid(self):
        handler = KdcReqMessageHandler(None, None, {"pvno": 5}, None)
        self.assertTrue(PvnoCheck(handler).check())

    def test_invalid(self):
        handler = KdcReqMessageHandler(None, None, {"pvno": 42}, None)
        self.assertFalse(PvnoCheck(handler).check())


class TestCnameFromKdcReqCheck(TestCase):
    def test_valid(self):
        handler = KdcReqMessageHandler(None, None, {"req-body": {"cname": "username"}}, None)
        self.assertTrue(CnameFromKdcReqCheck(handler).check())

    def test_invalid(self):
        handler = KdcReqMessageHandler(None, None, {"req-body": {}}, None)
        self.assertFalse(CnameFromKdcReqCheck(handler).check())
