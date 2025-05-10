"""SAML Source tests"""

from base64 import b64encode

from django.test import RequestFactory, TestCase
from django.urls import reverse

from authentik.common.tests import load_fixture
from authentik.core.tests.utils import create_test_flow
from authentik.crypto.generators import generate_id
from authentik.flows.planner import PLAN_CONTEXT_REDIRECT, FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.sources.saml.models import SAMLSource


class TestViews(TestCase):
    """Test SAML Views"""

    def setUp(self):
        self.factory = RequestFactory()
        self.source = SAMLSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            issuer="authentik",
            allow_idp_initiated=True,
            pre_authentication_flow=create_test_flow(),
        )

    def test_enroll(self):
        """Enroll"""
        flow = create_test_flow()
        self.source.enrollment_flow = flow
        self.source.save()

        response = self.client.post(
            reverse(
                "authentik_sources_saml:acs",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success.xml").encode()
                ).decode()
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        plan: FlowPlan = self.client.session.get(SESSION_KEY_PLAN)
        self.assertIsNotNone(plan)

    def test_enroll_redirect(self):
        """Enroll when attempting to access a provider"""
        initial_redirect = f"http://{generate_id()}"

        session = self.client.session
        old_plan = FlowPlan(generate_id())
        old_plan.context[PLAN_CONTEXT_REDIRECT] = initial_redirect
        session[SESSION_KEY_PLAN] = old_plan
        session.save()

        flow = create_test_flow()
        self.source.enrollment_flow = flow
        self.source.save()

        response = self.client.post(
            reverse(
                "authentik_sources_saml:acs",
                kwargs={
                    "source_slug": self.source.slug,
                },
            ),
            data={
                "SAMLResponse": b64encode(
                    load_fixture("fixtures/response_success.xml").encode()
                ).decode()
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug})
        )
        plan: FlowPlan = self.client.session.get(SESSION_KEY_PLAN)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.context.get(PLAN_CONTEXT_REDIRECT), initial_redirect)
