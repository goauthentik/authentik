"""admin tests"""
from django.test import TestCase
from django.test.client import RequestFactory

from authentik.admin.views.policies_bindings import PolicyBindingCreateView
from authentik.core.models import Application


class TestPolicyBindingView(TestCase):
    """Generic admin tests"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_without_get_param(self):
        """Test PolicyBindingCreateView without get params"""
        request = self.factory.get("/")
        view = PolicyBindingCreateView(request=request)
        self.assertEqual(view.get_initial(), {})

    def test_with_param(self):
        """Test PolicyBindingCreateView with get params"""
        target = Application.objects.create(name="test")
        request = self.factory.get("/", {"target": target.pk.hex})
        view = PolicyBindingCreateView(request=request)
        self.assertEqual(view.get_initial(), {"target": target, "order": 0})
