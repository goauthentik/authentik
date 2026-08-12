"""Tests for messages attached to challenges"""

from django.contrib.messages import add_message
from django.contrib.messages.constants import SUCCESS, WARNING
from django.contrib.messages.storage.session import SessionStorage
from django.http import HttpRequest, HttpResponse
from django.urls import reverse

from authentik.core.tests.utils import create_test_flow
from authentik.flows.challenge import Challenge, ChallengeResponse
from authentik.flows.models import FlowStageBinding, in_memory_stage
from authentik.flows.planner import FlowPlan
from authentik.flows.stage import ChallengeStageView, StageView
from authentik.flows.tests import FlowTestCase
from authentik.stages.dummy.models import DummyStage


class MessageStageView(StageView):
    """Stage which queues a message and continues to the next stage"""

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        add_message(request, SUCCESS, "stage message")
        return self.executor.stage_ok()


class MessageChallengeStageView(ChallengeStageView):
    """Stage which queues a message while rendering its challenge"""

    def get_challenge(self, *args, **kwargs) -> Challenge:
        add_message(self.request, WARNING, "challenge message")
        return Challenge(data={"component": "ak-stage-dummy"})

    def challenge_valid(self, response: ChallengeResponse) -> HttpResponse:
        return self.executor.stage_ok()


class TestFlowMessages(FlowTestCase):
    """Test messages attached to challenges"""

    def setUp(self):
        self.flow = create_test_flow()
        self.url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})

    def test_challenge(self):
        """Test message queued while the challenge is rendered"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.append_stage(in_memory_stage(MessageChallengeStageView))
        self.set_flow_plan(plan)

        response = self.client.get(self.url)
        self.assertStageResponse(
            response,
            self.flow,
            messages=[{"level": "warning", "message": "challenge message"}],
        )

    def test_challenge_not_repeated(self):
        """Test that a message is only ever attached to a single challenge"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.append_stage(in_memory_stage(MessageChallengeStageView))
        self.set_flow_plan(plan)

        self.client.get(self.url)
        # The stage queues a new message on every render, so the second challenge only
        # contains the message queued for it
        response = self.client.get(self.url)
        self.assertStageResponse(
            response,
            self.flow,
            messages=[{"level": "warning", "message": "challenge message"}],
        )

    def test_previous_stage(self):
        """Test message queued by a stage which doesn't render a challenge itself, it is
        attached to the challenge of the next stage"""
        FlowStageBinding.objects.create(
            target=self.flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.append_stage(in_memory_stage(MessageStageView))
        plan.append(FlowStageBinding.objects.filter(target=self.flow).first())
        self.set_flow_plan(plan)

        response = self.client.get(self.url, follow=True)
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-dummy",
            messages=[{"level": "success", "message": "stage message"}],
        )

    def test_redirect_challenge(self):
        """Test message queued by the last stage of a flow. The client navigates away as soon
        as it gets the redirect challenge the flow finishes with, so the message is left
        queued for the page we redirect to"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex)
        plan.append_stage(in_memory_stage(MessageStageView))
        self.set_flow_plan(plan)

        response = self.client.get(self.url)
        raw_response = self.assertStageResponse(response, component="xak-flow-redirect")
        self.assertNotIn("messages", raw_response)
        self.assertIn("stage message", self.client.session[SessionStorage.session_key])

    def test_no_messages(self):
        """Test that challenges without messages have an empty list"""
        FlowStageBinding.objects.create(
            target=self.flow, stage=DummyStage.objects.create(name="dummy"), order=0
        )

        response = self.client.get(self.url)
        self.assertStageResponse(response, self.flow, messages=[])
