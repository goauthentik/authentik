"""admin tests"""
from uuid import uuid4

from django import forms
from django.test import TestCase
from django.test.client import RequestFactory

from authentik.admin.views.stages_bindings import StageBindingCreateView
from authentik.flows.forms import FlowStageBindingForm
from authentik.flows.models import Flow


class TestStageBindingView(TestCase):
    """Generic admin tests"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_without_get_param(self):
        """Test StageBindingCreateView without get params"""
        request = self.factory.get("/")
        view = StageBindingCreateView(request=request)
        self.assertEqual(view.get_initial(), {})

    def test_with_params_invalid(self):
        """Test StageBindingCreateView with invalid get params"""
        request = self.factory.get("/", {"target": uuid4()})
        view = StageBindingCreateView(request=request)
        self.assertEqual(view.get_initial(), {})

    def test_with_params(self):
        """Test StageBindingCreateView with get params"""
        target = Flow.objects.create(name="test", slug="test")
        request = self.factory.get("/", {"target": target.pk.hex})
        view = StageBindingCreateView(request=request)
        self.assertEqual(view.get_initial(), {"target": target, "order": 0})

        self.assertTrue(
            isinstance(
                FlowStageBindingForm(initial={"target": "foo"}).fields["target"].widget,
                forms.HiddenInput,
            )
        )
