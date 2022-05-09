"""Test helpers"""
from json import loads
from typing import Any, Optional

from django.http.response import HttpResponse
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow


class FlowTestCase(APITestCase):
    """Helpers for testing flows and stages."""

    # pylint: disable=invalid-name
    def assertStageResponse(
        self,
        response: HttpResponse,
        flow: Optional[Flow] = None,
        user: Optional[User] = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Assert various attributes of a stage response"""
        self.assertEqual(response.status_code, 200)
        raw_response = loads(response.content.decode())
        self.assertIsNotNone(raw_response["component"])
        self.assertIsNotNone(raw_response["type"])
        if flow:
            self.assertIn("flow_info", raw_response)
            self.assertEqual(raw_response["flow_info"]["background"], flow.background_url)
            self.assertEqual(
                raw_response["flow_info"]["cancel_url"], reverse("authentik_flows:cancel")
            )
            # We don't check the flow title since it will most likely go
            # through ChallengeStageView.format_title() so might not match 1:1
            # self.assertEqual(raw_response["flow_info"]["title"], flow.title)
            self.assertIsNotNone(raw_response["flow_info"]["title"])
        if user:
            self.assertEqual(raw_response["pending_user"], user.username)
            self.assertEqual(raw_response["pending_user_avatar"], user.avatar)
        for key, expected in kwargs.items():
            self.assertEqual(raw_response[key], expected)
        return raw_response

    # pylint: disable=invalid-name
    def assertStageRedirects(self, response: HttpResponse, to: str) -> dict[str, Any]:
        """Wrapper around assertStageResponse that checks for a redirect"""
        return self.assertStageResponse(
            response, component="xak-flow-redirect", to=to, type=ChallengeTypes.REDIRECT.value
        )
