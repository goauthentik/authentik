"""flow views tests"""

from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_flow
<<<<<<< HEAD
from authentik.flows.tests import FlowTestCase
=======
from authentik.flows.planner import PLAN_CONTEXT_APPLICATION, FlowPlan
from authentik.flows.stage import PLAN_CONTEXT_PENDING_USER_IDENTIFIER
from authentik.flows.tests import APIFlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.flows.views.interface import FlowInterfaceView
>>>>>>> f1341f57c (flows: format titles correct on first render if possible (#27589))


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
<<<<<<< HEAD
        self.assertContains(response, '"title": "100% secure",')
=======
        self.assertContains(response, '<meta name="ak-flow-title" content="100% secure">')

    def test_title_plan_context(self):
        """Placeholders are filled from the plan in the session"""
        flow = create_test_flow()
        flow.title = "Sign in to %(app)s as %(user)s"
        flow.save()
        plan = FlowPlan(flow_pk=flow.pk.hex)
        plan.context[PLAN_CONTEXT_APPLICATION] = Application(name="Grafana")
        plan.context[PLAN_CONTEXT_PENDING_USER_IDENTIFIER] = "jdoe"
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        self.assertContains(
            response, '<meta name="ak-flow-title" content="Sign in to Grafana as jdoe">'
        )

    def test_title_plan_other_flow(self):
        """A plan for a different flow still fills placeholders"""
        flow = create_test_flow()
        flow.title = "Sign in to %(app)s"
        flow.save()
        plan = FlowPlan(flow_pk=create_test_flow().pk.hex)
        plan.context[PLAN_CONTEXT_APPLICATION] = Application(name="Grafana")
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        self.assertContains(response, '<meta name="ak-flow-title" content="Sign in to Grafana">')

    def test_title_plan_invalid_placeholder(self):
        """Unknown placeholders with a plan keep the original title"""
        flow = create_test_flow()
        flow.title = "Hello %(foo)s"
        flow.save()
        session = self.client.session
        session[SESSION_KEY_PLAN] = FlowPlan(flow_pk=flow.pk.hex)
        session.save()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        self.assertContains(response, '<meta name="ak-flow-title" content="Hello %(foo)s">')


class TestFlowInterfaceBackground(APIFlowTestCase):
    """Test the flow background on the interface page"""

    def test_themed_background(self):
        """A themed background renders its light variant, and its dark variant under
        data-theme="dark", before the flow executor loads"""
        flow = create_test_flow()
        flow.background = "/static/authentik/sources/kerberos/%(theme)s.png"
        flow.save()
        response = self.client.get(
            reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertRegex(
            content,
            r":root \{\s*--ak-global--background-image: "
            r'url\("http://testserver/static/authentik/sources/kerberos/light.png"\);',
        )
        self.assertRegex(
            content,
            r':root\[data-theme="dark"\] \{\s*--ak-global--background-image: '
            r'url\("http://testserver/static/authentik/sources/kerberos/dark.png"\);',
        )
>>>>>>> f1341f57c (flows: format titles correct on first render if possible (#27589))
