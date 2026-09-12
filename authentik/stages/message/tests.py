"""message tests"""

from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.models import FlowDesignation, FlowStageBinding
from authentik.flows.tests import FlowTestCase
from authentik.stages.message.models import MessageStage


class TestMessageStage(FlowTestCase):
    """Message tests"""

    def setUp(self) -> None:
        super().setUp()
        self.flow = create_test_flow(FlowDesignation.AUTHENTICATION)
        self.stage = MessageStage.objects.create(
            name="message",
            title="Test Title",
            message="Test Message",
        )
        FlowStageBinding.objects.create(
            target=self.flow,
            stage=self.stage,
            order=0,
        )

    def test_default_button_text(self) -> None:
        """Test that the challenge contains the configured message."""
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-message",
            name="message",
            title="Test Title",
            message="Test Message",
            button_text="",
        )

    def test_button_text_non_default(self) -> None:
        """Test that the challenge contains the configured string message."""
        self.stage.button_text = "Ok"
        self.stage.save(update_fields=["button_text"])
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-message",
            name="message",
            title="Test Title",
            message="Test Message",
            button_text="Ok",
        )

    def test_message_html_string(self) -> None:
        """Test that the challenge contains the configured html message."""
        self.stage.message = "<div style='color:red;'><p>Test Message</p></div>"
        self.stage.save(update_fields=["message"])
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-message",
            name="message",
            title="Test Title",
            message="<div style='color:red;'><p>Test Message</p></div>",
            button_text="",
        )

    def test_post(self) -> None:
        """Test that continuing completes the stage."""
        url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
