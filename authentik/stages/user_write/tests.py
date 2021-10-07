"""write tests"""
import string
from random import SystemRandom
from unittest.mock import patch

from django.urls import reverse
from django.utils.encoding import force_str
from rest_framework.test import APITestCase

from authentik.core.models import USER_ATTRIBUTE_SOURCES, Group, Source, User, UserSourceConnection
from authentik.core.sources.stage import PLAN_CONTEXT_SOURCES_CONNECTION
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.markers import StageMarker
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.models import UserWriteStage


class TestUserWriteStage(APITestCase):
    """Write tests"""

    def setUp(self):
        super().setUp()
        self.flow = Flow.objects.create(
            name="test-write",
            slug="test-write",
            designation=FlowDesignation.AUTHENTICATION,
        )
        self.group = Group.objects.create(name="test-group")
        self.stage = UserWriteStage.objects.create(
            name="write", create_users_as_inactive=True, create_users_group=self.group
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)
        self.source = Source.objects.create(name="fake_source")

    def test_user_create(self):
        """Test creation of user"""
        password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user",
            "name": "name",
            "email": "test@beryju.org",
            "password": password,
        }
        plan.context[PLAN_CONTEXT_SOURCES_CONNECTION] = UserSourceConnection(source=self.source)
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
        user_qs = User.objects.filter(username=plan.context[PLAN_CONTEXT_PROMPT]["username"])
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(password))
        self.assertEqual(list(user_qs.first().ak_groups.all()), [self.group])
        self.assertEqual(user_qs.first().attributes, {USER_ATTRIBUTE_SOURCES: [self.source.name]})

    def test_user_update(self):
        """Test update of existing user"""
        new_password = "".join(
            SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8)
        )
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = User.objects.create(
            username="unittest", email="test@beryju.org"
        )
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user-new",
            "password": new_password,
            "attribute.some.custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "xak-flow-redirect",
                "to": reverse("authentik_core:root-redirect"),
                "type": ChallengeTypes.REDIRECT.value,
            },
        )
        user_qs = User.objects.filter(username=plan.context[PLAN_CONTEXT_PROMPT]["username"])
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(new_password))
        self.assertEqual(user_qs.first().attributes["some"]["custom-attribute"], "test")
        self.assertNotIn("some_ignored_attribute", user_qs.first().attributes)

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_without_data(self):
        """Test without data results in error"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "ak-stage-access-denied",
                "error_message": None,
                "type": ChallengeTypes.NATIVE.value,
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                },
            },
        )

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_blank_username(self):
        """Test with blank username results in error"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "",
            "attribute_some-custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "ak-stage-access-denied",
                "error_message": None,
                "type": ChallengeTypes.NATIVE.value,
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                },
            },
        )

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_duplicate_data(self):
        """Test with duplicate data, should trigger error"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "akadmin",
            "attribute_some-custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            force_str(response.content),
            {
                "component": "ak-stage-access-denied",
                "error_message": None,
                "type": ChallengeTypes.NATIVE.value,
                "flow_info": {
                    "background": self.flow.background_url,
                    "cancel_url": reverse("authentik_flows:cancel"),
                    "title": "",
                },
            },
        )
