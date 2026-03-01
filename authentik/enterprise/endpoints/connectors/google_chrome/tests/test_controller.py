from json import dumps
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import RequestFactory
from authentik.endpoints.facts import OSFamily
from authentik.endpoints.models import Device
from authentik.enterprise.endpoints.connectors.google_chrome.controller import (
    HEADER_ACCESS_CHALLENGE,
    GoogleChromeController,
)
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.enterprise.providers.google_workspace.clients.test_http import MockHTTP
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import load_fixture


class TestGoogleChromeConnector(APITestCase):
    def setUp(self):
        self.connector = GoogleChromeConnector.objects.create(
            name=generate_id(), credentials={},
        )
        self.factory = RequestFactory()
        self.api_key = generate_id()

    def test_generate_challenge(self):
        req = self.factory.get("/")
        challenge = generate_id()
        http = MockHTTP()
        http.add_response(
            f"https://verifiedaccess.googleapis.com/v2/challenge:generate?key={self.api_key}&alt=json",
            {"challenge": challenge},
            method="POST",
        )
        with patch(
            "authentik.enterprise.endpoints.connectors.google_chrome.models.GoogleChromeConnector.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            controller = GoogleChromeController(self.connector)
            res = controller.generate_challenge(req)
            self.assertEqual(
                res["Location"],
                req.build_absolute_uri(
                    reverse("authentik_endpoints_connectors_google_chrome:chrome")
                ),
            )
            self.assertEqual(res.headers[HEADER_ACCESS_CHALLENGE], dumps({"challenge": challenge}))

    def test_validate_challenge(self):
        http = MockHTTP()
        http.add_response(
            f"https://verifiedaccess.googleapis.com/v2/challenge:verify?key={self.api_key}&alt=json",
            load_fixture("fixtures/host_macos.json"),
            method="POST",
        )
        with patch(
            "authentik.enterprise.endpoints.connectors.google_chrome.models.GoogleChromeConnector.google_credentials",
            MagicMock(return_value={"developerKey": self.api_key, "http": http}),
        ):
            controller = GoogleChromeController(self.connector)
            controller.validate_challenge(dumps("{}"))
        device = Device.objects.get(identifier="Z5DDF07GK6")
        self.assertIsNotNone(device)
        self.assertEqual(device.cached_facts.data["os"]["family"], OSFamily.macOS)
