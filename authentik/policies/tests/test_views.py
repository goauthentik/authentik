from django.http import Http404, HttpResponse
from django.test import TestCase
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, Provider
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_brand,
    create_test_flow,
    create_test_user,
)
from authentik.flows.models import Flow, FlowDesignation
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.policies.apps import BufferedPolicyAccessViewFlag
from authentik.policies.models import PolicyBinding
from authentik.policies.views import (
    QS_BUFFER_ID,
    SESSION_KEY_BUFFER,
    BufferedPolicyAccessView,
    BufferView,
    PolicyAccessView,
)
from authentik.tenants.flags import patch_flag


class TestPolicyViews(TestCase):
    """Test PolicyAccessView"""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_user()

    def test_pav(self):
        """Test simple policy access view"""
        provider = Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)

        class TestView(PolicyAccessView):
            def resolve_provider_application(self):
                self.provider = provider
                self.application = app

            def get(self, *args, **kwargs):
                return HttpResponse("foo")

        req = self.factory.get("/")
        req.user = self.user
        res = TestView.as_view()(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, b"foo")

    def test_pav_unauthenticated_no_flow(self):
        """Test simple policy access view (unauthenticated access, no authentication flow)"""
        Flow.objects.filter(designation=FlowDesignation.AUTHENTICATION).delete()
        provider = Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)

        class TestView(PolicyAccessView):
            def resolve_provider_application(self):
                self.provider = provider
                self.application = app

            def get(self, *args, **kwargs):
                return HttpResponse("foo")

        req = self.factory.get("/")
        req.brand = create_test_brand()
        with self.assertRaises(Http404):
            TestView.as_view()(req)

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_pav_unauthenticated_flow_no_acccess(self):
        """Test simple policy access view (unauthenticated access,
        authentication flow with policy)"""
        provider = Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        flow = Flow.objects.get(slug="default-authentication-flow")
        PolicyBinding.objects.create(
            target=flow, group=Group.objects.create(name=generate_id()), order=0
        )

        class TestView(PolicyAccessView):
            def resolve_provider_application(self):
                self.provider = provider
                self.application = app

            def get(self, *args, **kwargs):
                return HttpResponse("foo")

        req = self.factory.get("/")
        req.brand = create_test_brand(flow_authentication=flow)
        with self.assertRaises(Http404):
            TestView.as_view()(req)

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_pav_unauthenticated_next_param(self):
        """Test simple policy access view (unauthenticated access, with checking next param)"""
        provider = Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        flow = Flow.objects.get(slug="default-authentication-flow")

        class TestView(PolicyAccessView):
            def resolve_provider_application(self):
                self.provider = provider
                self.application = app

            def get(self, *args, **kwargs):
                return HttpResponse("foo")

        req = self.factory.get("/")
        req.brand = create_test_brand(flow_authentication=flow)
        res = TestView.as_view()(req)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/if/flow/default-authentication-flow/?next=%2F")

    @patch_flag(BufferedPolicyAccessViewFlag, True)
    def test_pav_buffer(self):
        """Test simple policy access view"""
        provider = Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        flow = create_test_flow(FlowDesignation.AUTHENTICATION)

        class TestView(BufferedPolicyAccessView):
            def resolve_provider_application(self):
                self.provider = provider
                self.application = app

            def get(self, *args, **kwargs):
                return HttpResponse("foo")

        req = self.factory.get("/")
        req.session[SESSION_KEY_PLAN] = FlowPlan(flow.pk)
        req.session.save()
        res = TestView.as_view()(req)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.url.startswith(reverse("authentik_policies:buffer")))

    @patch_flag(BufferedPolicyAccessViewFlag, True)
    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_pav_buffer_skip(self):
        """Test simple policy access view (skip buffer)"""
        provider = Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        flow = Flow.objects.get(slug="default-authentication-flow")

        class TestView(BufferedPolicyAccessView):
            def resolve_provider_application(self):
                self.provider = provider
                self.application = app

            def get(self, *args, **kwargs):
                return HttpResponse("foo")

        req = self.factory.get("/?skip_buffer=true")
        req.brand = create_test_brand(flow_authentication=flow)
        req.session[SESSION_KEY_PLAN] = FlowPlan(flow.pk)
        req.session.save()
        res = TestView.as_view()(req)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(
            res.url.startswith(reverse("authentik_core:if-flow", kwargs={"flow_slug": flow.slug}))
        )

    def test_buffer(self):
        """Test buffer view"""
        uid = generate_id()
        req = self.factory.get(f"/?{QS_BUFFER_ID}={uid}")
        ts = generate_id()
        req.session[SESSION_KEY_BUFFER % uid] = {
            "method": "get",
            "body": {},
            "url": f"/{ts}",
        }
        req.session.save()

        res = BufferView.as_view()(req)
        self.assertEqual(res.status_code, 200)
        self.assertIn(ts, res.render().content.decode())
