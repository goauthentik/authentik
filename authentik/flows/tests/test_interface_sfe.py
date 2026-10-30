"""flow views tests"""

from django.test import RequestFactory
from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.tests import APIFlowTestCase
from authentik.flows.views.interface import FlowInterfaceView


class TestFlowInterfaceSimple(APIFlowTestCase):
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

    def test_ie(self):
        """Test Internet Explorer/Trident"""
        self.assertTrue(
            self.needs_sfe("Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko")
        )
        self.assertTrue(
            self.needs_sfe("Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)")
        )

    def test_edge_legacy(self):
        """Test legacy edge"""
        self.assertTrue(
            self.needs_sfe(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, "
                "like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362"
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

    def test_old_chrome(self):
        """Unaffected browsers keep the default flow executor"""
        self.assertTrue(
            self.needs_sfe(
                "Mozilla/5.0 (Linux; Android 11; sdk_gphone_x86_64) AppleWebKit/537.36 (KHTML, "
                "like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36"
            )
        )

    def test_unknown_user_agent(self):
        """A user agent without a parseable version keeps the default flow executor"""
        self.assertFalse(self.needs_sfe(""))


class TestFlowInterfaceTitle(APIFlowTestCase):
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
        self.assertContains(response, '<meta name="ak-flow-title" content="Welcome to">')
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
        self.assertContains(response, '<meta name="ak-flow-title" content="100% secure">')
