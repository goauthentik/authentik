"""Stage binding policy tests"""

from unittest.mock import MagicMock, patch

from django.db import OperationalError
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.flows.models import Flow, FlowDesignation, FlowStageBinding
from authentik.flows.tests import APIFlowTestCase
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.policies.process import PolicyProcess
from authentik.stages.authenticator_totp.models import TOTPDevice
from authentik.stages.deny.models import DenyStage
from authentik.stages.dummy.models import DummyStage
from authentik.stages.identification.models import IdentificationStage
from authentik.stages.password.models import PasswordStage


class TestStageBindingPolicies(APIFlowTestCase):
    """Stage binding policy tests"""

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    @patch(
        "authentik.policies.process.cache",
        MagicMock(set=MagicMock(side_effect=OperationalError())),
    )
    def test_reevaluate_keep_cache_error(self):
        """Stage is kept when its policy result can't be cached"""
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(exec_url, {"uid_field": user.username}, follow=True)
        self.assertStageResponse(response, component="ak-stage-password")

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    @patch(
        "authentik.policies.process.cache",
        MagicMock(set=MagicMock(side_effect=OperationalError())),
    )
    def test_reevaluate_keep_cache_error_failure_result_false(self):
        """Policy result, not the failure result, applies when the result can't be cached"""
        PolicyBinding.objects.filter(
            policy__name="default-authentication-flow-password-stage"
        ).update(failure_result=False)
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(exec_url, {"uid_field": user.username}, follow=True)
        self.assertStageResponse(response, component="ak-stage-password")

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    @patch.object(PolicyProcess, "create_event", MagicMock(side_effect=OperationalError()))
    def test_reevaluate_keep_logging_error(self):
        """Stage is kept when its policy execution can't be logged"""
        ExpressionPolicy.objects.filter(name="default-authentication-flow-password-stage").update(
            execution_logging=True
        )
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(exec_url, {"uid_field": user.username}, follow=True)
        self.assertStageResponse(response, component="ak-stage-password")

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    @patch.object(PolicyProcess, "create_event", MagicMock(side_effect=OperationalError()))
    def test_reevaluate_keep_logging_error_failure_result_false(self):
        """Policy result, not the failure result, applies when the execution can't be logged"""
        ExpressionPolicy.objects.filter(name="default-authentication-flow-password-stage").update(
            execution_logging=True
        )
        PolicyBinding.objects.filter(
            policy__name="default-authentication-flow-password-stage"
        ).update(failure_result=False)
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(exec_url, {"uid_field": user.username}, follow=True)
        self.assertStageResponse(response, component="ak-stage-password")

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    @patch.object(ExpressionPolicy, "passes", MagicMock(side_effect=OperationalError()))
    def test_reevaluate_keep_policy_error(self):
        """Stage is kept when its policy can't be evaluated"""
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(exec_url, {"uid_field": user.username}, follow=True)
        self.assertStageResponse(response, component="ak-stage-password")

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    @patch.object(PolicyProcess, "create_event", MagicMock(side_effect=OperationalError()))
    def test_reevaluate_keep_dry_run_error(self):
        """Stage is kept when its only binding is a dry-run binding that errors"""
        PolicyBinding.objects.filter(
            policy__name="default-authentication-flow-password-stage"
        ).update(dry_run=True, failure_result=False)
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(exec_url, {"uid_field": user.username}, follow=True)
        self.assertStageResponse(response, component="ak-stage-password")

    @patch(
        "authentik.policies.process.cache",
        MagicMock(set=MagicMock(side_effect=OperationalError())),
    )
    def test_plan_keep_cache_error(self):
        """Stage evaluated during planning is kept when its policy result can't be cached"""
        flow = create_test_flow(FlowDesignation.AUTHORIZATION)
        deny_binding = FlowStageBinding.objects.create(
            target=flow,
            stage=DenyStage.objects.create(name=generate_id()),
            order=0,
            evaluate_on_plan=True,
            re_evaluate_policies=False,
        )
        PolicyBinding.objects.create(
            target=deny_binding,
            policy=ExpressionPolicy.objects.create(name=generate_id(), expression="return True"),
            order=0,
            failure_result=True,
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=1,
        )
        self.client.force_login(create_test_user())

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-access-denied")

    @patch(
        "authentik.policies.process.cache",
        MagicMock(set=MagicMock(side_effect=OperationalError())),
    )
    def test_plan_keep_cache_error_failure_result_false(self):
        """Policy result, not the failure result, applies during planning when the result can't
        be cached"""
        flow = create_test_flow(FlowDesignation.AUTHORIZATION)
        deny_binding = FlowStageBinding.objects.create(
            target=flow,
            stage=DenyStage.objects.create(name=generate_id()),
            order=0,
            evaluate_on_plan=True,
            re_evaluate_policies=False,
        )
        PolicyBinding.objects.create(
            target=deny_binding,
            policy=ExpressionPolicy.objects.create(name=generate_id(), expression="return True"),
            order=0,
            failure_result=False,
        )
        FlowStageBinding.objects.create(
            target=flow,
            stage=DummyStage.objects.create(name=generate_id()),
            order=1,
        )
        self.client.force_login(create_test_user())

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-access-denied")

    @apply_blueprint("default/flow-default-authentication-flow.yaml")
    def test_reevaluate_remove_authenticated(self):
        """Password stage is removed once the identification stage checked the password"""
        IdentificationStage.objects.filter(name="default-authentication-identification").update(
            password_stage=PasswordStage.objects.get(name="default-authentication-password")
        )
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_user()
        TOTPDevice.objects.create(user=user, confirmed=True)

        exec_url = reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug})
        response = self.client.get(exec_url)
        self.assertStageResponse(response, component="ak-stage-identification")
        response = self.client.post(
            exec_url, {"uid_field": user.username, "password": user.username}, follow=True
        )
        self.assertStageResponse(response, component="ak-stage-authenticator-validate")
