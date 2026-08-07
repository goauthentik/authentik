from plistlib import PlistFormat, loads

from defusedxml.lxml import fromstring
from django.test import RequestFactory
from rest_framework.test import APITestCase

from authentik.endpoints.connectors.agent.models import (
    AgentConnector,
    ApplePSSOAuthenticationPolicy,
    EnrollmentToken,
)
from authentik.endpoints.facts import OSFamily
from authentik.lib.generators import generate_id


def _platform_sso(config: str) -> dict:
    """Return the PlatformSSO dict from a generated macOS profile."""
    data = loads(config, fmt=PlistFormat.FMT_XML)
    return next(
        payload["PlatformSSO"]
        for payload in data["PayloadContent"]
        if payload.get("PayloadType") == "com.apple.extensiblesso"
    )


class TestAgentConnector(APITestCase):

    def setUp(self):
        self.connector = AgentConnector.objects.create(
            name=generate_id(),
        )
        self.token = EnrollmentToken.objects.create(name=generate_id(), connector=self.connector)
        self.factory = RequestFactory()

    def test_generate_mdm_macos(self):
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        self.assertIsNotNone(res.validated_data)
        data = loads(res.validated_data["config"], fmt=PlistFormat.FMT_XML)
        self.assertEqual(data["PayloadContent"][0]["RegistrationToken"], self.token.key)
        self.assertEqual(data["PayloadContent"][0]["URL"], "http://testserver/")
        # With the default configuration Platform SSO stays passive: no enforcement
        # policies are emitted, only the always-present login frequency.
        psso = _platform_sso(res.validated_data["config"])
        self.assertNotIn("LoginPolicy", psso)
        self.assertNotIn("UnlockPolicy", psso)
        self.assertNotIn("FileVaultPolicy", psso)
        self.assertEqual(psso["LoginFrequency"], 64800)

    def test_generate_mdm_macos_psso_policies(self):
        """Configured Apple Platform SSO policies must appear in the generated profile as
        arrays of policy strings (matching ee/psso/example.mobileconfig); policies left at
        their default must be omitted so Platform SSO keeps its passive behaviour."""
        self.connector.apple_psso_login_policy = ApplePSSOAuthenticationPolicy.REQUIRE
        self.connector.apple_psso_unlock_policy = ApplePSSOAuthenticationPolicy.ATTEMPT
        self.connector.apple_psso_login_frequency = 7200
        self.connector.save()
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.macOS, request, self.token
        )
        psso = _platform_sso(res.validated_data["config"])
        self.assertEqual(psso["LoginPolicy"], ["RequireAuthentication"])
        self.assertEqual(psso["UnlockPolicy"], ["AttemptAuthentication"])
        self.assertEqual(psso["LoginFrequency"], 7200)
        # filevault left at the default "none" -> key omitted entirely
        self.assertNotIn("FileVaultPolicy", psso)

    def test_generate_mdm_windows(self):
        request = self.factory.get("/")
        res = self.connector.controller(self.connector).generate_mdm_config(
            OSFamily.windows, request, self.token
        )
        self.assertIsNotNone(res.validated_data)
        config = res.validated_data["config"]
        fromstring(f"<root>{config}</root>")
        self.assertIn(self.token.key, config)
        self.assertIn("http://testserver/", config)
