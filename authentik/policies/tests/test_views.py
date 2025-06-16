from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse

from authentik.core.models import Application, Provider
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.flows.models import FlowDesignation
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import dummy_get_response
from authentik.policies.views import (
    QS_BUFFER_ID,
    SESSION_KEY_BUFFER,
    BufferedPolicyAccessView,
    BufferView,
    PolicyAccessView,
)


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
        req.user = AnonymousUser()
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(req)
        req.session[SESSION_KEY_PLAN] = FlowPlan(flow.pk)
        req.session.save()
        res = TestView.as_view()(req)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.url.startswith(reverse("authentik_policies:buffer")))

    def test_pav_buffer_skip(self):
        """Test simple policy access view (skip buffer)"""
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

        req = self.factory.get("/?skip_buffer=true")
        req.user = AnonymousUser()
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(req)
        req.session[SESSION_KEY_PLAN] = FlowPlan(flow.pk)
        req.session.save()
        res = TestView.as_view()(req)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.url.startswith(reverse("authentik_flows:default-authentication")))

    def test_buffer(self):
        """Test buffer view"""
        uid = generate_id()
        req = self.factory.get(f"/?{QS_BUFFER_ID}={uid}")
        req.user = AnonymousUser()
        middleware = SessionMiddleware(dummy_get_response)
        middleware.process_request(req)
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
