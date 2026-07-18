from plistlib import PlistFormat, loads

from defusedxml.lxml import fromstring
from django.test import RequestFactory
from rest_framework.test import APITestCase

from authentik.endpoints.connectors.agent.models import AgentConnector, EnrollmentToken
from authentik.endpoints.facts import OSFamily
from authentik.lib.generators import generate_id


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
