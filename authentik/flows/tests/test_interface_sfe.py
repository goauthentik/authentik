"""flow views tests"""

from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.tests import FlowTestCase


class TestFlowInterfaceTitle(FlowTestCase):
    """Test flow title placeholders on the interface page"""

    def test_title_placeholder(self):
        """Placeholders are blanked as no plan context exists yet"""
        flow = create_test_flow()
        flow.title = "Welcome to %(app)s"
        flow.save()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"title": "Welcome to",')
        flow.refresh_from_db()
        self.assertEqual(flow.title, "Welcome to %(app)s")

    def test_title_literal_percent(self):
        """Titles with a bare percent sign are left as-is"""
        flow = create_test_flow()
        flow.title = "100% secure"
        flow.save()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        self.assertContains(response, '"title": "100% secure",')
