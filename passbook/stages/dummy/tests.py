"""dummy tests"""
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils.encoding import force_text

from passbook.core.models import User
from passbook.flows.models import Flow, FlowDesignation, FlowStageBinding
from passbook.stages.dummy.forms import DummyStageForm
from passbook.stages.dummy.models import DummyStage


class TestDummyStage(TestCase):
    """Dummy tests"""

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="unittest", email="test@beryju.org")
        self.client = Client()

        self.flow = Flow.objects.create(
            name="test-dummy",
            slug="test-dummy",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.stage = DummyStage.objects.create(name="dummy",)
        FlowStageBinding.objects.create(
            target=self.flow, stage=self.stage, order=0,
        )

    def test_valid_render(self):
        """Test that View renders correctly"""
        response = self.client.get(
            reverse(
                "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Test with valid email, check that URL redirects back to itself"""
        url = reverse(
            "passbook_flows:flow-executor", kwargs={"flow_slug": self.flow.slug}
        )
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_text(response.content),
            {"type": "redirect", "to": reverse("passbook_core:overview")},
        )

    def test_form(self):
        """Test Form"""
        data = {"name": "test"}
        self.assertEqual(DummyStageForm(data).is_valid(), True)
