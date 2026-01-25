from django.http import Http404, HttpResponse
from django.test import TestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application, Group, Provider
from authentik.core.tests.utils import (
    RequestFactory,
    create_test_brand,
    create_test_user,
)
from authentik.flows.models import Flow, FlowDesignation
from authentik.lib.generators import generate_id
from authentik.policies.models import PolicyBinding
from authentik.policies.views import (
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
