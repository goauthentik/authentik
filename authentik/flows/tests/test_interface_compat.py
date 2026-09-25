"""Compatibility-mode rendering of the flow interface"""

from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.tests import FlowTestCase

SHADY_DOM_MARKER = b'data-id="shady-dom"'


class TestFlowInterfaceCompatibility(FlowTestCase):
    """The ShadyDOM shim is emitted for compatibility mode, from the flow or `?compat`"""

    def setUp(self) -> None:
        super().setUp()
        self.flow = create_test_flow()

    def flow_url(self, query: str = "") -> str:
        url = reverse("authentik_core:if-flow", kwargs={"flow_slug": self.flow.slug})
        return f"{url}{query}"

    def test_off_by_default(self):
        """A flow without compatibility mode renders no shim"""
        response = self.client.get(self.flow_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SHADY_DOM_MARKER, response.content)

    def test_flow_setting_enables(self):
        """The flow's own setting still turns the shim on"""
        self.flow.compatibility_mode = True
        self.flow.save()

        response = self.client.get(self.flow_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn(SHADY_DOM_MARKER, response.content)

    def test_query_parameter_enables(self):
        """`?compat` turns the shim on without touching the flow"""
        response = self.client.get(self.flow_url("?compat"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(SHADY_DOM_MARKER, response.content)

        self.flow.refresh_from_db()
        self.assertFalse(
            self.flow.compatibility_mode,
            "The query parameter must not persist onto the flow",
        )

    def test_inspector_still_wins(self):
        """The inspector suppresses the shim, as it did for the flow setting"""
        response = self.client.get(self.flow_url("?compat&inspector"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(SHADY_DOM_MARKER, response.content)
