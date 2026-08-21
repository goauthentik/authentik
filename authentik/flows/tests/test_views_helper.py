"""flow views tests"""

from django.test import RequestFactory
from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.flows.views.interface import FlowInterfaceView


class TestHelperView(FlowTestCase):
    """Test helper views logic"""

    def test_default_view(self):
        """Test that ToDefaultFlow returns the expected URL"""
        Flow.objects.filter(designation=FlowDesignation.INVALIDATION).delete()
        flow = create_test_flow(FlowDesignation.INVALIDATION)
        response = self.client.get(
            reverse("authentik_flows:default-invalidation"),
        )
        expected_url = reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    def test_default_view_invalid_plan(self):
        """Test that ToDefaultFlow returns the expected URL (with an invalid plan)"""
        Flow.objects.filter(designation=FlowDesignation.INVALIDATION).delete()
        flow = create_test_flow(FlowDesignation.INVALIDATION)
        plan = FlowPlan(flow_pk=flow.pk.hex + "aa")
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_flows:default-invalidation"),
        )
        expected_url = reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)


class TestFlowInterfaceCompat(FlowTestCase):
    """Test which flow executor is selected for a given user agent"""

    def needs_sfe(self, user_agent: str) -> bool:
        """Run compat_needs_sfe() against a request carrying user_agent"""
        request = RequestFactory().get("/", HTTP_USER_AGENT=user_agent)
        view = FlowInterfaceView()
        view.request = request
        return view.compat_needs_sfe()

    def test_old_webkit(self):
        """WebKit older than 16.4 cannot parse the default flow executor"""
        self.assertTrue(
            self.needs_sfe(
                "Mozilla/5.0 (iPad; CPU OS 15_8 like Mac OS X) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/15.6.8 Mobile/15E148 Safari/604.1"
            )
        )

    def test_old_ios_other_browser(self):
        """Browsers on iOS use the system WebKit, so the iOS version decides"""
        self.assertTrue(
            self.needs_sfe(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) CriOS/119.0 Mobile/15E148 Safari/604.1"
            )
        )

    def test_old_ipados_desktop_mode(self):
        """iPadOS in desktop mode reports itself as Safari on macOS"""
        self.assertTrue(
            self.needs_sfe(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/15.6 Safari/605.1.15"
            )
        )

    def test_current_webkit(self):
        """WebKit 16.4 and newer parses the default flow executor"""
        self.assertFalse(
            self.needs_sfe(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 "
                "(KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1"
            )
        )

    def test_current_chrome(self):
        """Unaffected browsers keep the default flow executor"""
        self.assertFalse(
            self.needs_sfe(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
            )
        )

    def test_unknown_user_agent(self):
        """A user agent without a parseable version keeps the default flow executor"""
        self.assertFalse(self.needs_sfe(""))
