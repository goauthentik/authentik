"""Test helpers"""

from collections.abc import Callable, Generator
from contextlib import contextmanager
from json import loads
from typing import Any
from unittest.mock import MagicMock, patch

from django.http import HttpRequest
from django.http.response import HttpResponse
from django.test import TestCase
from django.urls.base import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.flows.models import Flow
from authentik.flows.planner import FlowPlan
from authentik.flows.storage import FlowExecution


class _FlowTestCase:
    """Helpers for testing flows and stages."""

    def assertStageResponse(
        self,
        response: HttpResponse,
        flow: Flow | None = None,
        user: User | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Assert various attributes of a stage response"""
        self.assertEqual(response.status_code, 200)
        raw_response = loads(response.content.decode())
        self.assertIsNotNone(raw_response["component"])
        if flow:
            self.assertIn("flow_info", raw_response)
            self.assertTrue(
                raw_response["flow_info"]["cancel_url"].startswith(
                    reverse("authentik_flows:cancel")
                )
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

    def get_flow_execution(self) -> FlowExecution:
        """Flow execution of the test client,
        call `.request.session.save()` after saving the execution"""
        request = HttpRequest()
        # client.session returns a fresh store on every access, keep a single one
        request.session = self.client.session
        return FlowExecution(request)

    def get_flow_plan(self) -> FlowPlan | None:
        return self.get_flow_execution().plan

    def set_flow_plan(self, plan: FlowPlan):
        execution = self.get_flow_execution()
        execution.replace(plan)
        execution.request.session.save()

    def assertStageRedirects(self, response: HttpResponse, to: str) -> dict[str, Any]:
        """Wrapper around assertStageResponse that checks for a redirect"""
        return self.assertStageResponse(response, component="xak-flow-redirect", to=to)

    @contextmanager
    def assertFlowFinishes(self) -> Generator[Callable[[], FlowPlan]]:
        """Capture the flow plan before the flow finishes and return it"""
        try:
            with patch("authentik.flows.views.executor.FlowExecutorView.cancel", MagicMock()):
                yield self.get_flow_plan
        finally:
            pass


class FlowTestCase(_FlowTestCase, TestCase):
    """Flow test case with a standard Django client"""


class APIFlowTestCase(_FlowTestCase, APITestCase):
    """Flow test case with a DRF client"""
