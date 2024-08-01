"""Test Source flow_manager group update stage"""

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from guardian.utils import get_anonymous_user

from authentik.core.models import Group, SourceGroupMatchingModes, SourceUserMatchingModes, User
from authentik.core.sources.flow_manager import PLAN_CONTEXT_SOURCE_GROUPS, Action
from authentik.core.sources.stage import PostSourceStage
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import in_memory_stage
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, PLAN_CONTEXT_SOURCE, FlowPlan
from authentik.flows.tests import FlowTestCase
from authentik.flows.views.executor import SESSION_KEY_PLAN, FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.lib.tests.utils import get_request
from authentik.policies.denied import AccessDeniedResponse
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.sources.oauth.models import OAuthSource, GroupOAuthSourceConnection
from authentik.sources.oauth.views.callback import OAuthSourceFlowManager
from authentik.core.sources.flow_manager import GroupUpdateStage


class TestSourceFlowManager(FlowTestCase):
    """Test Source flow_manager group update stage"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.authentication_flow = create_test_flow()
        self.enrollment_flow = create_test_flow()
        self.source: OAuthSource = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            authentication_flow=self.authentication_flow,
            enrollment_flow=self.enrollment_flow,
        )
        self.identifier = generate_id()
        self.user = create_test_admin_user()

    def test_nonexistant_group(self):
        request = self.factory.get("/")
        stage = GroupUpdateStage(
            FlowExecutorView(
                current_stage=in_memory_stage(GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection),
                plan=FlowPlan(
                    flow_pk=generate_id(),
                    context={
                        PLAN_CONTEXT_SOURCE: self.source,
                        PLAN_CONTEXT_PENDING_USER: self.user,
                        PLAN_CONTEXT_SOURCE_GROUPS: {
                            "group 1": {
                                "name": "group 1",
                            },
                        },
                    },
                ),
            ),
            request=request,
        )
        self.assertTrue(stage.handle_groups())
        self.assertTrue(Group.objects.filter(name="group 1").exists())
        self.assertTrue(self.user.ak_groups.filter(name="group 1").exists())
        self.assertTrue(GroupOAuthSourceConnection.objects.filter(group=Group.objects.get(name="group 1"), source=self.source).exists())

    def test_nonexistant_group_name_link(self):
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_LINK
        self.source.save()

        request = self.factory.get("/")
        stage = GroupUpdateStage(
            FlowExecutorView(
                current_stage=in_memory_stage(GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection),
                plan=FlowPlan(
                    flow_pk=generate_id(),
                    context={
                        PLAN_CONTEXT_SOURCE: self.source,
                        PLAN_CONTEXT_PENDING_USER: self.user,
                        PLAN_CONTEXT_SOURCE_GROUPS: {
                            "group 1": {
                                "name": "group 1",
                            },
                        },
                    },
                ),
            ),
            request=request,
        )
        self.assertTrue(stage.handle_groups())
        self.assertTrue(Group.objects.filter(name="group 1").exists())
        self.assertTrue(self.user.ak_groups.filter(name="group 1").exists())
        self.assertTrue(GroupOAuthSourceConnection.objects.filter(group=Group.objects.get(name="group 1"), source=self.source).exists())

    def test_existant_group_name_link(self):
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_LINK
        self.source.save()
        group = Group.objects.create(name="group 1")

        request = self.factory.get("/")
        stage = GroupUpdateStage(
            FlowExecutorView(
                current_stage=in_memory_stage(GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection),
                plan=FlowPlan(
                    flow_pk=generate_id(),
                    context={
                        PLAN_CONTEXT_SOURCE: self.source,
                        PLAN_CONTEXT_PENDING_USER: self.user,
                        PLAN_CONTEXT_SOURCE_GROUPS: {
                            "group 1": {
                                "name": "group 1",
                            },
                        },
                    },
                ),
            ),
            request=request,
        )
        self.assertTrue(stage.handle_groups())
        self.assertTrue(Group.objects.filter(name="group 1").exists())
        self.assertTrue(self.user.ak_groups.filter(name="group 1").exists())
        self.assertTrue(GroupOAuthSourceConnection.objects.filter(group=group, source=self.source).exists())

    def test_nonexistant_group_name_deny(self):
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_DENY
        self.source.save()

        request = self.factory.get("/")
        stage = GroupUpdateStage(
            FlowExecutorView(
                current_stage=in_memory_stage(GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection),
                plan=FlowPlan(
                    flow_pk=generate_id(),
                    context={
                        PLAN_CONTEXT_SOURCE: self.source,
                        PLAN_CONTEXT_PENDING_USER: self.user,
                        PLAN_CONTEXT_SOURCE_GROUPS: {
                            "group 1": {
                                "name": "group 1",
                            },
                        },
                    },
                ),
            ),
            request=request,
        )
        self.assertTrue(stage.handle_groups())
        self.assertTrue(Group.objects.filter(name="group 1").exists())
        self.assertTrue(self.user.ak_groups.filter(name="group 1").exists())
        self.assertTrue(GroupOAuthSourceConnection.objects.filter(group=Group.objects.get(name="group 1"), source=self.source).exists())

    def test_existant_group_name_link(self):
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_DENY
        self.source.save()
        group = Group.objects.create(name="group 1")

        request = self.factory.get("/")
        stage = GroupUpdateStage(
            FlowExecutorView(
                current_stage=in_memory_stage(GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection),
                plan=FlowPlan(
                    flow_pk=generate_id(),
                    context={
                        PLAN_CONTEXT_SOURCE: self.source,
                        PLAN_CONTEXT_PENDING_USER: self.user,
                        PLAN_CONTEXT_SOURCE_GROUPS: {
                            "group 1": {
                                "name": "group 1",
                            },
                        },
                    },
                ),
            ),
            request=request,
        )
        self.assertFalse(stage.handle_groups())
        self.assertFalse(self.user.ak_groups.filter(name="group 1").exists())
        self.assertFalse(GroupOAuthSourceConnection.objects.filter(group=group, source=self.source).exists())

    def test_group_updates(self):
        self.source.group_matching_mode = SourceGroupMatchingModes.NAME_LINK
        self.source.save()

        other_group = Group.objects.create(name="other group")
        old_group = Group.objects.create(name="old group")
        new_group = Group.objects.create(name="new group")
        self.user.ak_groups.set([other_group, old_group])
        GroupOAuthSourceConnection.objects.create(group=old_group, source=self.source, identifier=old_group.name)
        GroupOAuthSourceConnection.objects.create(group=new_group, source=self.source, identifier=new_group.name)


        request = self.factory.get("/")
        stage = GroupUpdateStage(
            FlowExecutorView(
                current_stage=in_memory_stage(GroupUpdateStage, group_connection_type=GroupOAuthSourceConnection),
                plan=FlowPlan(
                    flow_pk=generate_id(),
                    context={
                        PLAN_CONTEXT_SOURCE: self.source,
                        PLAN_CONTEXT_PENDING_USER: self.user,
                        PLAN_CONTEXT_SOURCE_GROUPS: {
                            "new group": {
                                "name": "new group",
                            },
                        },
                    },
                ),
            ),
            request=request,
        )
        self.assertTrue(stage.handle_groups())
        self.assertFalse(self.user.ak_groups.filter(name="old group").exists())
        self.assertTrue(self.user.ak_groups.filter(name="other group").exists())
        self.assertTrue(self.user.ak_groups.filter(name="new group").exists())
        self.assertEqual(self.user.ak_groups.count(), 2)
