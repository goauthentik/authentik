"""write tests"""
from unittest.mock import patch

from django.urls import reverse

from authentik.core.models import USER_ATTRIBUTE_SOURCES, Group, Source, User, UserSourceConnection
from authentik.core.sources.stage import PLAN_CONTEXT_SOURCES_CONNECTION
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.markers import StageMarker
from authentik.flows.models import FlowStageBinding
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.tests.test_executor import TO_STAGE_RESPONSE_MOCK
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_key
from authentik.stages.prompt.stage import PLAN_CONTEXT_PROMPT
from authentik.stages.user_write.models import UserCreationMode, UserWriteStage
from authentik.stages.user_write.stage import PLAN_CONTEXT_GROUPS, UserWriteStageView


class TestUserWriteStage(FlowTestCase):
    """Write tests"""

    def setUp(self):
        super().setUp()
        self.flow = create_test_flow()
        self.group = Group.objects.create(name="test-group")
        self.other_group = Group.objects.create(name="other-group")
        self.stage: UserWriteStage = UserWriteStage.objects.create(
            name="write", create_users_as_inactive=True, create_users_group=self.group
        )
        self.binding = FlowStageBinding.objects.create(target=self.flow, stage=self.stage, order=2)
        self.source = Source.objects.create(name="fake_source")
        self.user = create_test_admin_user()

    def test_user_create(self):
        """Test creation of user"""
        password = generate_key()

        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user",
            "name": "name",
            "email": "test@goauthentik.io",
            "password": password,
        }
        plan.context[PLAN_CONTEXT_GROUPS] = [self.other_group]
        plan.context[PLAN_CONTEXT_SOURCES_CONNECTION] = UserSourceConnection(source=self.source)
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        user_qs = User.objects.filter(username=plan.context[PLAN_CONTEXT_PROMPT]["username"])
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(password))
        self.assertEqual(
            list(user_qs.first().ak_groups.order_by("name")), [self.other_group, self.group]
        )
        self.assertEqual(user_qs.first().attributes, {USER_ATTRIBUTE_SOURCES: [self.source.name]})

    def test_user_update(self):
        """Test update of existing user"""
        new_password = generate_key()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        plan.context[PLAN_CONTEXT_PENDING_USER] = User.objects.create(
            username="unittest", email="test@goauthentik.io"
        )
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "test-user-new",
            "password": new_password,
            "attributes.some.custom-attribute": "test",
            "attributes": {
                "foo": "bar",
            },
            "some_ignored_attribute": "bar",
        }
        session = self.client.session
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.post(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertEqual(response.status_code, 200)
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        user_qs = User.objects.filter(username=plan.context[PLAN_CONTEXT_PROMPT]["username"])
        self.assertTrue(user_qs.exists())
        self.assertTrue(user_qs.first().check_password(new_password))
        self.assertEqual(user_qs.first().attributes["some"]["custom-attribute"], "test")
        self.assertEqual(user_qs.first().attributes["foo"], "bar")
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

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
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

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
        )

    def test_authenticated_no_user(self):
        """Test user in session and none in plan"""
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        self.client.force_login(self.user)
        session = self.client.session
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "foo",
            "attribute_some-custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageRedirects(response, reverse("authentik_core:root-redirect"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "foo")

    def test_no_create(self):
        """Test can_create_users set to false"""
        self.stage.user_creation_mode = UserCreationMode.NEVER_CREATE
        self.stage.save()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": "foo",
            "attribute_some-custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )
        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
        )

    @patch(
        "authentik.flows.views.executor.to_stage_response",
        TO_STAGE_RESPONSE_MOCK,
    )
    def test_duplicate_data(self):
        """Test with duplicate data, should trigger error"""
        user = create_test_admin_user()
        plan = FlowPlan(flow_pk=self.flow.pk.hex, bindings=[self.binding], markers=[StageMarker()])
        session = self.client.session
        plan.context[PLAN_CONTEXT_PROMPT] = {
            "username": user.username,
            "attribute_some-custom-attribute": "test",
            "some_ignored_attribute": "bar",
        }
        session[SESSION_KEY_PLAN] = plan
        session.save()

        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": self.flow.slug})
        )

        self.assertStageResponse(
            response,
            self.flow,
            component="ak-stage-access-denied",
        )

    def test_write_attribute(self):
        """Test write_attribute"""
        user = create_test_admin_user()
        user.attributes = {
            "foo": "bar",
            "baz": {
                "qwer": [
                    "quox",
                ]
            },
        }
        user.save()
        UserWriteStageView.write_attribute(user, "attributes.foo", "baz")
        self.assertEqual(
            user.attributes,
            {
                "foo": "baz",
                "baz": {
                    "qwer": [
                        "quox",
                    ]
                },
            },
        )
        UserWriteStageView.write_attribute(user, "attributes.foob.bar", "baz")
        self.assertEqual(
            user.attributes,
            {
                "foo": "baz",
                "foob": {
                    "bar": "baz",
                },
                "baz": {
                    "qwer": [
                        "quox",
                    ]
                },
            },
        )
